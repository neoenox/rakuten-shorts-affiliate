"""Muse(https://muse.ai/) に完成動画を送ってレビューを受ける。生CDP版。

usage:
  python scripts/muse_review.py <slug> [--dry-run] [--timeout 600] [--note "追記"]

前提: レビュー用Chrome（--user-data-dir=C:\\Users\\neoen\\.chrome-automation --remote-debugging-port=9223）で
      muse.ai にログイン済みであること。
出力: out/muse_reply_<slug>.txt
"""
import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import requests
import websocket

ROOT = Path(__file__).resolve().parents[1]
PORT = 9223
MARK = '問題点は時刻つきで具体的にお願いします。'
FFMPEG = r'E:\rekishikaisetu-honnoji\tools\ffmpeg\bin\ffmpeg.exe'

TEMPLATE = ('この動画のレビューをお願いします。添付は、{topic}のYouTube Shorts（約{sec}秒・縦1080x1920）です。'
            '映像はAI生成のイメージ・自作イラスト・自作の模式図で、商品画像は使っていません。'
            '楽天アフィリエイトの広告を含み、PR表記を全編に入れています。{note}'
            'まず、ナレーションを文字に起こしてください（台本と照合します）。'
            '見てほしい点は、(1)字幕と音声の一致、(2)読み間違い・音割れ・無音、(3)文字の重なり・はみ出し・見切れ、'
            '(4)数字と出典の整合、(5)冒頭1〜3秒の引き、(6)図の分かりやすさ、(7)公開してよいか。'
            + MARK)


def ensure_chrome():
    """レビュー用Chromeが落ちていたら、最小化で起動する（chrome_launch.py に任せる）。"""
    try:
        requests.get(f'http://127.0.0.1:{PORT}/json/version', timeout=3)
        return
    except Exception:
        pass
    launcher = ROOT / 'scripts' / 'chrome_launch.py'
    subprocess.run([sys.executable, str(launcher), 'review'], check=False, timeout=180)


class C:
    def __init__(self, port=PORT):
        ensure_chrome()
        v = requests.get(f'http://127.0.0.1:{port}/json/version', timeout=10).json()
        self.ws = websocket.create_connection(v['webSocketDebuggerUrl'], timeout=180)
        self.n = 0

    def call(self, method, params=None, session=None, timeout=120):
        self.n += 1
        msg = {'id': self.n, 'method': method, 'params': params or {}}
        if session:
            msg['sessionId'] = session
        self.ws.settimeout(timeout)
        self.ws.send(json.dumps(msg))
        while True:
            r = json.loads(self.ws.recv())
            if r.get('id') == self.n:
                return r

    def ev(self, sid, expr, timeout=120):
        r = self.call('Runtime.evaluate', {'expression': expr, 'returnByValue': True, 'awaitPromise': True},
                      session=sid, timeout=timeout)
        return r.get('result', {}).get('result', {}).get('value')

    def open(self, url, match):
        pages = [t for t in self.call('Target.getTargets')['result']['targetInfos'] if t.get('type') == 'page']
        t = [x for x in pages if match in (x.get('url') or '')]
        tid = t[-1]['targetId'] if t else self.call('Target.createTarget', {'url': url})['result']['targetId']
        sid = self.call('Target.attachToTarget', {'targetId': tid, 'flatten': True})['result']['sessionId']
        self.call('Target.activateTarget', {'targetId': tid})
        return sid

    def find_files(self, sid):
        doc = self.call('DOM.getDocument', {'depth': -1, 'pierce': True}, session=sid)['result']['root']
        out = []

        def walk(node):
            if (node.get('nodeName') or '').upper() == 'INPUT':
                flat = node.get('attributes') or []
                attrs = {flat[i]: flat[i + 1] for i in range(0, len(flat) - 1, 2)}
                if attrs.get('type') == 'file':
                    out.append({'nodeId': node['nodeId'], 'accept': attrs.get('accept', '')})
            for ch in node.get('children') or []:
                walk(ch)
            for sr in node.get('shadowRoots') or []:
                walk(sr)

        walk(doc)
        return out


def compress(src, slug):
    out = ROOT / 'out' / f'muse_{slug}.mp4'
    # レビュー用コピーは低ビットレートAACで符号化overshootが出るため、1.5dB下げて作る。
    # 本編は -14 LUFS / true peak -1.9 dBFS で管理している（Museが見る「0.0dB」はこのコピー側の値）。
    subprocess.run([FFMPEG, '-v', 'error', '-y', '-i', str(src), '-vf', 'scale=360:-2',
                    '-c:v', 'libx264', '-crf', '30', '-preset', 'fast',
                    '-af', 'volume=-1.5dB', '-c:a', 'aac', '-b:a', '96k', str(out)],
                   check=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('slug')
    ap.add_argument('--video', default='')
    ap.add_argument('--topic', default='')
    ap.add_argument('--note', default='')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--timeout', type=int, default=600)
    a = ap.parse_args()

    data = json.loads((ROOT / 'shorts' / a.slug / 'result.json').read_text(encoding='utf-8'))
    src = Path(a.video) if a.video else ROOT / 'out' / 'draft' / f'{a.slug}_DRAFT.mp4'
    if not src.exists():
        sys.exit(f'動画が見つからない: {src}')
    sec = round(data.get('duration_sec') or 0)
    msg = TEMPLATE.format(topic=a.topic or data.get('title', a.slug), sec=sec, note=(a.note + ' ' if a.note else ''))

    clip = compress(src, a.slug)
    print(f'圧縮: {clip.name} ({clip.stat().st_size / 1e6:.1f} MB)')

    c = C()
    sid = c.open('https://muse.ai/', 'muse.ai')
    for _ in range(40):
        if c.ev(sid, "!!document.querySelector('input[type=file]')") and c.ev(sid, "!!document.querySelector('[contenteditable=true], textarea, [role=textbox]')"):
            break
        time.sleep(2)
    time.sleep(2)

    files = c.find_files(sid)
    if not files:
        sys.exit('ファイル入力が見つからない（ログインしていない可能性）')
    c.call('DOM.setFileInputFiles', {'files': [str(clip)], 'nodeId': files[0]['nodeId']}, session=sid)
    print('添付した')
    time.sleep(3)

    box = c.ev(sid, """(() => { const el = document.querySelector('[contenteditable=true], textarea, [role=textbox]');
      if (!el) return null; el.focus(); const r = el.getBoundingClientRect();
      return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2), tag: el.tagName}; })()""")
    if not box:
        sys.exit('入力欄が見つからない')
    c.call('Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': box['x'], 'y': box['y'], 'button': 'left', 'clickCount': 1}, session=sid)
    c.call('Input.dispatchMouseEvent', {'type': 'mouseReleased', 'x': box['x'], 'y': box['y'], 'button': 'left', 'clickCount': 1}, session=sid)
    time.sleep(1)
    c.call('Input.insertText', {'text': msg}, session=sid)
    time.sleep(1)
    got = c.ev(sid, """(() => { const el = document.querySelector('[contenteditable=true], textarea, [role=textbox]');
      return el ? (el.value !== undefined ? el.value : el.innerText).length : -1; })()""")
    print(f'入力 {got} 文字 / 依頼 {len(msg)} 文字')

    if a.dry_run:
        print('--dry-run: 送信しない')
        return 0

    # 送信（Enter → 空にならなければボタン）
    c.call('Input.dispatchKeyEvent', {'type': 'keyDown', 'key': 'Enter', 'windowsVirtualKeyCode': 13, 'text': '\r'}, session=sid)
    c.call('Input.dispatchKeyEvent', {'type': 'keyUp', 'key': 'Enter', 'windowsVirtualKeyCode': 13}, session=sid)
    time.sleep(4)
    left = c.ev(sid, """(() => { const el = document.querySelector('[contenteditable=true], textarea, [role=textbox]');
      return el ? (el.value !== undefined ? el.value : el.innerText).trim().length : -1; })()""")
    if left not in (0, -1):
        p = c.ev(sid, """(() => { const b = document.querySelector('button[aria-label*="送信"], button[aria-label*="Send"]');
          if (!b) return null; const r = b.getBoundingClientRect();
          return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)}; })()""")
        if p:
            c.call('Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': p['x'], 'y': p['y'], 'button': 'left', 'clickCount': 1}, session=sid)
            c.call('Input.dispatchMouseEvent', {'type': 'mouseReleased', 'x': p['x'], 'y': p['y'], 'button': 'left', 'clickCount': 1}, session=sid)
    print('送信した。返答を待つ')

    t0 = time.time()
    last, stable = '', 0
    while time.time() - t0 < a.timeout:
        body = c.ev(sid, 'document.body.innerText') or ''
        i = body.rfind(MARK)
        txt = (body[i + len(MARK):] if i >= 0 else '').strip()
        if txt and txt == last:
            stable += 1
            if stable >= 3 and len(txt) > 200:
                break
        else:
            stable = 0
        last = txt
        time.sleep(5)
    out = ROOT / 'out' / f'muse_reply_{a.slug}.txt'
    out.write_text(last + '\n', encoding='utf-8')
    print(f'返答 {len(last)} 文字（{time.time() - t0:.0f}秒）-> {out}')
    c.ws.close()


if __name__ == '__main__':
    sys.exit(main() or 0)
