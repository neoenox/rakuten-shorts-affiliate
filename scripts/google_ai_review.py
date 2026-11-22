"""Google AI モード（google.com/ai）に完成動画を送ってレビューを受ける。生CDP版。

usage:
  python scripts/google_ai_review.py <slug> [--dry-run] [--timeout 600] [--note "追記"]

前提: レビュー用Chrome（--user-data-dir=C:\\Users\\neoen\\.chrome-automation --remote-debugging-port=9223）
      で Google にログイン済みであること。
出力: out/ai_reply_<slug>.txt（返答本文）。レビューの採否は人が shorts/<slug>/review_ai.md に残す。
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import requests

from cdp_client import Client
from gate import ffmpeg_bin

ROOT = Path(__file__).resolve().parents[1]
PORT = 9223
AI_URL = 'https://www.google.com/ai/'
MARK = '問題点は時刻つきで具体的にお願いします。'

TEMPLATE = (
    'この動画のレビューをお願いします。添付は、{topic}のYouTube Shorts（約{sec}秒・縦1080x1920）です。'
    '映像は自作のイラスト・模式図で、商品画像は使っていません。'
    '楽天アフィリエイトの広告を含み、PR表記を全編に入れています。{note}'
    'まず、ナレーションを文字に起こしてください（台本と照合します）。'
    '見てほしい点は、(1)字幕と音声の一致、(2)読み間違い・音割れ・無音、(3)文字の重なり・はみ出し・見切れ、'
    '(4)数字と出典の整合、(5)冒頭1〜3秒の引き、(6)図の分かりやすさ、(7)このまま公開してよいか（公開可／要修正）。'
    + MARK
)

# 回答の末尾に付く UI 文言と、生成中のプレースホルダ。これらは返答として受理しない。
TRAILING_UI = (
    'AI モードが質問について考えています',
    'AI モードが回答を生成しています',
    'AI は不正確な情報を表示することがあるため',
    'パーソナライズなしで試す',
    'All items removed from input context.',
    '前のプロンプトにスキップする',
)

TOOLS = 'ファイルとツールを追加し、モデルを選択します'
ADD_FILE = 'ファイルを追加'
SEND = '送信'


def ensure_chrome():
    """レビュー用Chromeが落ちていたら、最小化で起動する。"""
    try:
        requests.get(f'http://127.0.0.1:{PORT}/json/version', timeout=3)
        return
    except Exception:
        pass
    launcher = ROOT / 'scripts' / 'chrome_launch.py'
    subprocess.run([sys.executable, str(launcher), 'review'], check=False, timeout=180)


class C(Client):
    def __init__(self, port=PORT):
        ensure_chrome()
        super().__init__(port=port, ws_timeout=180, call_timeout=120)

    def click_aria(self, sid, label):
        """aria-label が一致する可視ボタンを JS で押す（Polymer のメニューも開く）。"""
        return bool(self.ev(sid, """(() => {
          const b = [...document.querySelectorAll('button, [role=button]')]
            .find(x => x.getAttribute('aria-label') === %s && x.getBoundingClientRect().width > 0);
          if (!b) return false;
          b.click(); return true;
        })()""" % json.dumps(label, ensure_ascii=False)))

    def click_text(self, sid, text):
        return bool(self.ev(sid, """(() => {
          const e = [...document.querySelectorAll('*')]
            .find(x => x.children.length === 0 && (x.textContent || '').trim() === %s
                        && x.getBoundingClientRect().width > 0);
          if (!e) return false;
          e.click(); return true;
        })()""" % json.dumps(text, ensure_ascii=False)))

    def find_file_inputs(self, sid):
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

    def composer_point(self, sid):
        return self.ev(sid, """(() => {
          const t = [...document.querySelectorAll('textarea')]
            .find(x => x.getBoundingClientRect().width > 0);
          if (!t) return null;
          const r = t.getBoundingClientRect();
          return {x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2)};
        })()""")


def reply_ready(txt, last, stable, min_chars):
    return bool(txt and txt == last and stable >= 3 and len(txt) >= min_chars)


def extract_reply(body, mark=MARK):
    """会話本文から最後の依頼マーカー以降の回答だけを切り出す。"""
    if not body:
        return ''
    i = body.rfind(mark)
    if i < 0:
        return ''
    txt = body[i + len(mark):]
    for cut in TRAILING_UI:
        j = txt.find(cut)
        if j >= 0:
            txt = txt[:j]
    return txt.strip()


def compress(src, slug):
    out = ROOT / 'out' / f'ai_{slug}.mp4'
    subprocess.run([ffmpeg_bin(), '-v', 'error', '-y', '-i', str(src), '-vf', 'scale=360:-2',
                    '-c:v', 'libx264', '-crf', '30', '-preset', 'fast',
                    '-af', 'volume=-1.5dB', '-c:a', 'aac', '-b:a', '96k', str(out)],
                   check=True)
    return out


def main():
    ap = argparse.ArgumentParser(description='Google AI モードで完成動画をレビューする')
    ap.add_argument('slug')
    ap.add_argument('--video', default='')
    ap.add_argument('--note', default='')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--timeout', type=int, default=600)
    ap.add_argument('--min-chars', type=int, default=50, help='返答とみなす最小文字数')
    a = ap.parse_args()

    data = json.loads((ROOT / 'shorts' / a.slug / 'result.json').read_text(encoding='utf-8'))
    src = Path(a.video) if a.video else ROOT / 'out' / 'draft' / f'{a.slug}_DRAFT.mp4'
    if not src.exists():
        sys.exit(f'動画が見つからない: {src}')
    sec = round(data.get('duration_sec') or 0)
    msg = TEMPLATE.format(topic=data.get('title', a.slug), sec=sec,
                          note=(a.note + ' ' if a.note else ''))
    if a.dry_run:
        print(msg)
        return 0

    clip = compress(src, a.slug)
    print(f'圧縮: {clip.name} ({clip.stat().st_size / 1e6:.1f} MB)')

    c = C()
    sid = c.open(AI_URL, 'udm=50')
    # 新規スレッドを確実にするため、AI モードの入口へ一度移動する（DOM のボタンだけだと
    # 直前の添付が残ることがある）。
    c.call('Page.navigate', {'url': AI_URL}, session=sid)
    time.sleep(6)
    if not c.click_aria(sid, TOOLS):
        sys.exit('ファイルとツールのボタンが見つからない（ログインを確認）')
    time.sleep(1)
    if not c.click_text(sid, ADD_FILE):
        sys.exit('ファイルを追加が見つからない')
    time.sleep(1)
    files = c.find_file_inputs(sid)
    target = next((f for f in files if not f['accept']), None)
    if not target:
        sys.exit('アップロード用のファイル入力が見つからない')
    c.call('DOM.setFileInputFiles', {'files': [str(clip)], 'nodeId': target['nodeId']}, session=sid)
    print('添付した')
    # ファイルの取り込みが終わるまで待つ（ここが早いと入力が捨てられる）
    for _ in range(30):
        # チップは折り返して表示されることがあるので、先頭の識別子で判定する
        if clip.stem[:8] in (c.ev(sid, 'document.body.innerText') or ''):
            break
        time.sleep(2)
    # アップロードが 0% のまま進まないことがある（Google 側の一時的な不調）。
    # このまま待つと送信ボタンが出ないため、早めに失敗を返す。
    for _ in range(30):
        progress = c.ev(sid, """(() => { const e = document.querySelector('[data-progressvalue]');
          return e ? e.getAttribute('data-progressvalue') : null; })()""")
        if progress is None or progress != '0':
            break
        time.sleep(2)
    else:
        sys.exit('ファイルのアップロードが開始されませんでした（Google AI モードを再読み込みして再実行）')
    time.sleep(3)

    p = c.composer_point(sid)
    if not p:
        sys.exit('質問欄が見つからない')
    c.rclick(sid, p['x'], p['y'])
    c.call('Input.insertText', {'text': msg}, session=sid)
    time.sleep(1)
    got = c.ev(sid, """(() => { const t = [...document.querySelectorAll('textarea')]
      .find(x => x.getBoundingClientRect().width > 0); return t ? t.value.length : 0; })()""")
    if not got:
        sys.exit('質問が入力されなかった')
    # 実マウス相当で押す（JS の .click() では送信されないことがある）
    sp = c.ev(sid, """(() => { const b = [...document.querySelectorAll('button')]
      .find(x => x.getAttribute('aria-label') === '送信' && x.getBoundingClientRect().width > 0);
      if (!b) return null; const r = b.getBoundingClientRect();
      return {x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2),
              d: b.hasAttribute('disabled')}; })()""")
    if not sp or sp.get('d'):
        sys.exit('送信ボタンが押せない')
    c.rclick(sid, sp['x'], sp['y'])
    print('送信した。返答を待つ')

    t0 = time.time()
    last, stable = '', 0
    while time.time() - t0 < a.timeout:
        body = c.ev(sid, 'document.body.innerText') or ''
        txt = extract_reply(body)
        if txt and txt == last:
            stable += 1
            if reply_ready(txt, last, stable, a.min_chars):
                break
        else:
            stable = 0
        last = txt
        time.sleep(5)
    out = ROOT / 'out' / f'ai_reply_{a.slug}.txt'
    out.write_text(last + '\n', encoding='utf-8')
    print(f'返答 {len(last)} 文字（{time.time() - t0:.0f}秒）-> {out}')
    c.close()
    return 0


if __name__ == '__main__':
    sys.exit(main() or 0)
