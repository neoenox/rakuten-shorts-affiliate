"""Shorts を YouTube Studio にアップロードする（生CDP・実クリック）。

usage:
  python scripts/upload_short.py <slug> [--publish]

前提:
  - 分離Chromeが CDP 9222 で起動していること（docs/CHANNEL_SETUP.md）
  - out/draft/<slug>_DRAFT.mp4 / _thumb.jpg / _description.md が存在すること

挙動:
  - 既定は「非公開」で保存する。--publish を付けると保存後に公開へ切り替える。
  - 「1日のアップロード数の上限」を検出したら、その場で中止して理由を表示する。
  - 各ステップのボタンは、見えて有効になるまで待ってから実マウス相当で押す
    （JSの .click() では Polymer の状態が更新されない）。
"""
import argparse
import json
import sys
import time
from pathlib import Path

import requests
import websocket

CDP_URL = 'http://127.0.0.1:9222'
CH = 'UCBQ8nx5q0_P9NrtStUkSTEg'
ROOT = Path(__file__).resolve().parents[1]

LIMIT_MARKERS = ('1 日のアップロード数の上限', 'アップロード数の上限に達しました')


def log(*a):
    print(*a, flush=True)


class CDP:
    def __init__(self):
        v = requests.get(CDP_URL + '/json/version', timeout=10).json()
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

    def rclick(self, sid, x, y):
        self.call('Input.dispatchMouseEvent', {'type': 'mouseMoved', 'x': x, 'y': y}, session=sid)
        self.call('Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1}, session=sid)
        self.call('Input.dispatchMouseEvent', {'type': 'mouseReleased', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1}, session=sid)

    def rect(self, sid, selector):
        return self.ev(sid, """(() => { const e = document.querySelector(%s); if (!e) return null;
          const r = e.getBoundingClientRect();
          return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2), w: Math.round(r.width),
                  d: e.hasAttribute('disabled'), vh: innerHeight}; })()""" % json.dumps(selector))

    def click_when_ready(self, sid, selector, timeout=120, label=''):
        t0 = time.time()
        while time.time() - t0 < timeout:
            p = self.rect(sid, selector)
            if p and p['w'] > 0 and not p['d']:
                if 0 < p['y'] < p['vh']:
                    self.rclick(sid, p['x'], p['y'])
                    log(f'  {label}: clicked ({p["x"]},{p["y"]})')
                    return True
                self.ev(sid, """(() => { const e = document.querySelector(%s); if (e) e.scrollIntoView({block:'center'}); })()""" % json.dumps(selector))
                time.sleep(1)
                continue
            time.sleep(2)
        log(f'  {label}: 押せませんでした')
        return False

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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('slug')
    ap.add_argument('--publish', action='store_true')
    a = ap.parse_args()

    py = a.slug + '_DRAFT'
    video = ROOT / 'out' / 'draft' / (py + '.mp4')
    thumb = ROOT / 'out' / 'draft' / (py + '_thumb.jpg')
    desc = ROOT / 'out' / 'draft' / (py + '_description.md')
    for p in (video, desc):
        if not p.exists():
            sys.exit(f'見つかりません: {p}')
    title = json.loads((ROOT / 'shorts' / a.slug / 'result.json').read_text(encoding='utf-8'))['title']
    text = desc.read_text(encoding='utf-8')

    c = CDP()
    tid = c.call('Target.createTarget', {'url': f'https://studio.youtube.com/channel/{CH}/videos/upload'})['result']['targetId']
    sid = c.call('Target.attachToTarget', {'targetId': tid, 'flatten': True})['result']['sessionId']
    c.call('Target.activateTarget', {'targetId': tid})
    for _ in range(40):
        if 'コンテンツ' in (c.ev(sid, 'document.body.innerText') or ''):
            break
        time.sleep(2)

    for _ in range(3):
        c.ev(sid, """(() => { for (const b of document.querySelectorAll('#upload-button')) {
          if (b.getBoundingClientRect().width > 0) { b.click(); return; } } })()""")
        time.sleep(5)
        files = c.find_file_inputs(sid)
        if files:
            break
    if not files:
        sys.exit('アップロードダイアログが開きませんでした')
    vi = [f for f in files if 'image' not in f['accept']]
    c.call('DOM.setFileInputFiles', {'files': [str(video)], 'nodeId': vi[0]['nodeId']}, session=sid)
    log('ファイルを設定しました')

    for _ in range(60):
        if c.ev(sid, "!!document.querySelector('#title-textarea #textbox')"):
            break
        time.sleep(2)

    c.ev(sid, """(() => { const el = document.querySelector('#title-textarea #textbox'); if (!el) return;
      el.focus(); document.execCommand('selectAll', false, null);
      document.execCommand('insertText', false, %s); })()""" % json.dumps(title))
    c.ev(sid, """(() => { const el = document.querySelector('ytcp-video-description #textbox'); if (!el) return;
      el.focus(); document.execCommand('selectAll', false, null);
      document.execCommand('insertText', false, %s); })()""" % json.dumps(text))
    log('タイトルと説明を設定しました')

    if thumb.exists():
        files = c.find_file_inputs(sid)
        imgs = [f for f in files if 'image' in f['accept']]
        if imgs:
            c.call('DOM.setFileInputFiles', {'files': [str(thumb)], 'nodeId': imgs[0]['nodeId']}, session=sid)
            time.sleep(5)
            log('サムネイルを設定しました')

    # 上限チェック
    body = c.ev(sid, 'document.body.innerText') or ''
    if any(m in body for m in LIMIT_MARKERS):
        log('!! 1日のアップロード上限に達しています（24時間待つかワンタイム認証が必要）')
        sys.exit(2)

    time.sleep(3)
    c.click_when_ready(sid, '#next-button', 120, '次へ(詳細)')
    time.sleep(6)

    rad = c.ev(sid, """(() => { const rs = Array.from(document.querySelectorAll('tp-yt-paper-radio-button')).filter(r => r.getBoundingClientRect().width > 0);
      for (const r of rs) if ((r.innerText || '').indexOf('いいえ、子ども向けではありません') >= 0) {
        const b = r.getBoundingClientRect(); return {x: Math.round(b.x + 20), y: Math.round(b.y + b.height/2)}; }
      return null; })()""")
    if rad:
        c.rclick(sid, rad['x'], rad['y'])
        log('  子ども向け: いいえ')
    time.sleep(3)
    c.click_when_ready(sid, '#next-button', 120, '次へ(要素)')

    for _ in range(40):
        t = c.ev(sid, 'document.body.innerText') or ''
        if '問題は検出されません' in t or 'チェックが完了しました' in t:
            log('  チェック完了')
            break
        time.sleep(5)
    time.sleep(3)
    c.click_when_ready(sid, '#next-button', 90, '次へ(公開設定)')

    for _ in range(30):
        if '限定公開' in (c.ev(sid, 'document.body.innerText') or ''):
            break
        time.sleep(3)

    target = '公開' if a.publish else '非公開'
    rad = c.ev(sid, """(() => { const rs = Array.from(document.querySelectorAll('tp-yt-paper-radio-button')).filter(r => r.getBoundingClientRect().width > 0);
      const p = rs.find(r => (r.innerText || '').trim() === %s);
      if (!p) return null; const b = p.getBoundingClientRect();
      return {checked: p.getAttribute('aria-checked'), x: Math.round(b.x + 20), y: Math.round(b.y + b.height/2)}; })()""" % json.dumps(target))
    if rad and rad.get('checked') != 'true':
        c.rclick(sid, rad['x'], rad['y'])
        time.sleep(3)
        log(f'  公開設定: {target}')

    c.click_when_ready(sid, '#save-button', 90, '保存')
    time.sleep(10)
    tail = (c.ev(sid, 'document.body.innerText.slice(-200)') or '').replace('\n', ' / ')
    log('保存後の表示:', tail)
    c.ws.close()


if __name__ == '__main__':
    main()

