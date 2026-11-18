"""台本（result.json）を ChatGPT / Gemini に査読させる。生CDP。

usage:
  python scripts/script_review.py <slug>                    # 両方に送る
  python scripts/script_review.py <slug> --target chatgpt    # 片方だけ
  python scripts/script_review.py <slug> --dry-run           # 依頼文を表示するだけ

前提: レビュー用Chrome（--user-data-dir=C:\\Users\\neoen\\.chrome-automation --remote-debugging-port=9223）
      に ChatGPT / Gemini でログイン済みであること。
出力: shorts/<slug>/review_chatgpt.md, shorts/<slug>/review_gemini.md
"""
import argparse
import json
import sys
import time
from pathlib import Path

import requests
import websocket

ROOT = Path(__file__).resolve().parents[1]
MARK = '===ここまでが台本です==='
PORT = 9223

TARGETS = {
    'chatgpt': {
        'url': 'https://chatgpt.com/',
        'match': 'chatgpt.com',
        'composer': 'div.ProseMirror[contenteditable="true"], #prompt-textarea',
        'send': 'button[data-testid="send-button"], button[aria-label*="送信"], button[aria-label*="Send"]',
        'reply': 'div[data-message-author-role="assistant"]',
        'busy': 'button[data-testid="stop-button"], button[aria-label*="停止"]',
    },
    'gemini': {
        'url': 'https://gemini.google.com/app',
        'match': 'gemini.google.com',
        'composer': 'rich-textarea div[contenteditable="true"], div[contenteditable="true"]',
        'send': 'button[aria-label*="送信"], button[aria-label*="Send"], button.send-button',
        'reply': 'model-response, message-content, .model-response-text',
        'busy': 'button[aria-label*="停止"], button[aria-label*="Stop"]',
        'enter_first': True,
    },
}


class C:
    def __init__(self, port=PORT):
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
        res = r.get('result', {})
        if 'exceptionDetails' in res:
            return {'__exc__': json.dumps(res['exceptionDetails'], ensure_ascii=False)[:300]}
        return res.get('result', {}).get('value')

    def pages(self):
        return [t for t in self.call('Target.getTargets')['result']['targetInfos'] if t.get('type') == 'page']

    def open(self, url, match):
        t = [x for x in self.pages() if match in (x.get('url') or '')]
        if t:
            tid = t[-1]['targetId']
        else:
            tid = self.call('Target.createTarget', {'url': url})['result']['targetId']
        sid = self.call('Target.attachToTarget', {'targetId': tid, 'flatten': True})['result']['sessionId']
        self.call('Target.activateTarget', {'targetId': tid})
        return sid


def build_prompt(slug, data, brief_text=''):
    scenes = data.get('scenes', [])
    lines = []
    total = data.get('duration_sec') or 0
    for i, sc in enumerate(scenes, 1):
        lines.append(f"{i}. ({sc.get('start')}〜{sc.get('end')}秒) ナレーション: {sc.get('narration')}")
        cap = sc.get('caption') or []
        if cap:
            lines.append(f"   テロップ: {' / '.join(cap)}")
        if sc.get('visual'):
            lines.append(f"   画面: {sc.get('visual')}")
    claims = data.get('claims', [])
    claim_lines = []
    for c in claims:
        claim_lines.append(f"[{c.get('id')}] {c.get('statement')}\n    出典: {c.get('source_url')}\n    確認メモ: {c.get('evidence_note', '')[:220]}")

    parts = [
        'あなたは、YouTube Shorts の台本の査読者です。以下の台本を、公開前の確認として評価してください。',
        '',
        '【守ってほしいこと】',
        '・台本を書き直さないでください。指摘と改善案の列挙だけにしてください。',
        '・新しい事実を挙げる場合は、必ず出典URLを付けてください。出典が無い場合は「確認できず」と書いてください。',
        '・断定できないことは「自信が低い」と明記してください。',
        '',
        '【動画の前提】',
        f'・長さ {total:.0f}秒の Shorts（縦1080x1920）。',
        '・商品画像は使えないため、映像はAI生成のイメージ・自作イラスト・自作の模式図のみ。',
        '・楽天アフィリエイトの広告を含む。PR表記は全編に入れている。商品名は説明欄に書く方式。',
        '・数字は公的資料の試算で、条件（地域・機種・単価）を画面に出す方針。',
        '',
        '【評価の観点】',
        'A. 事実の正確さ（数値・条件・帰属。資料の記載と食い違っていないか）',
        'B. 出典と主張の対応（その主張を、その出典で支えられるか。足りない根拠はどれか）',
        'C. 聞きやすさ（音声合成で読み間違えそうな語、同音異義、数字の読み、1文の長さ）',
        'D. 構成と引き（最初の3秒で引きつけるか、結論の回収、テンポ）',
        'E. 抜けている文脈・誤解を招く表現（前提の欠落、断定しすぎ、比較の不公平）',
        '',
        '【出力形式】',
        '1. 総評（「このまま公開」「直してから公開」「作り直し」のいずれか）と理由を3行以内。',
        '2. 指摘の一覧（表は使わず、1件ずつ「重大度: 高/中/低」「箇所: シーン番号か文」「指摘: …」「根拠: …」の4行で箇条書き）',
        '3. 問題ないと判断した点',
        '4. 自信の低い判断',
        '',
        '（表は使わないでください。見出しと箇条書きだけで結構です。）',
        '',
        f'【動画の題材】{data.get("title")}',
        f'【フック】{data.get("hook", "")}',
        '',
        '【台本】',
        '\n'.join(lines),
        '',
        '【主張と出典】',
        '\n'.join(claim_lines),
    ]
    if brief_text.strip():
        parts += ['', '【取材メモ（brief.yaml）】', brief_text.strip()[:2500]]
    parts += ['', MARK]
    return '\n'.join(parts)


def send(c, target, prompt, timeout=300):
    cfg = TARGETS[target]
    sid = c.open(cfg['url'], cfg['match'])

    for _ in range(40):
        if c.ev(sid, f'!!document.querySelector({json.dumps(cfg["composer"])})'):
            break
        time.sleep(2)
    else:
        return None, '入力欄が見つからない（ログインしていない可能性）'

    # 入力
    ok = c.ev(sid, """(() => {
      const el = document.querySelector(%s);
      if (!el) return 'no composer';
      el.focus();
      const dt = new DataTransfer();
      document.execCommand('selectAll', false, null);
      document.execCommand('delete', false, null);
      el.dispatchEvent(new ClipboardEvent('paste', {clipboardData: dt, bubbles: true, cancelable: true}));
      return 'ready';
    })()""" % json.dumps(cfg['composer']))
    # 長文は insertText で入れる（execCommand('insertText') は改行で切れることがある）
    c.ev(sid, """(() => { const el = document.querySelector(%s); if (el) el.focus(); })()""" % json.dumps(cfg['composer']))
    c.call('Input.insertText', {'text': prompt}, session=sid)
    time.sleep(1)
    got = c.ev(sid, """(() => { const el = document.querySelector(%s);
      if (!el) return -1; return (el.value !== undefined ? el.value : el.innerText).length; })()""" % json.dumps(cfg['composer']))
    print(f'  {target}: 入力 {got} 文字 / 依頼 {len(prompt)} 文字')

    # 送信（Gemini は Enter のほうが確実）
    if cfg.get('enter_first'):
        c.call('Input.dispatchKeyEvent', {'type': 'keyDown', 'key': 'Enter', 'windowsVirtualKeyCode': 13, 'text': '\r'}, session=sid)
        c.call('Input.dispatchKeyEvent', {'type': 'keyUp', 'key': 'Enter', 'windowsVirtualKeyCode': 13}, session=sid)
        time.sleep(4)
        left = c.ev(sid, """(() => { const el = document.querySelector(%s);
          if (!el) return -1; return (el.value !== undefined ? el.value : el.innerText).trim().length; })()""" % json.dumps(cfg['composer']))
        if left == 0:
            return wait_reply(c, sid, cfg, timeout)
    sent = False
    for _ in range(10):
        p = c.ev(sid, """(() => { const b = document.querySelector(%s);
          if (!b) return null; const r = b.getBoundingClientRect();
          return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2), w: Math.round(r.width),
                  d: b.disabled || b.getAttribute('aria-disabled') === 'true'}; })()""" % json.dumps(cfg['send']))
        if p and p.get('w', 0) > 0 and not p.get('d'):
            c.call('Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': p['x'], 'y': p['y'], 'button': 'left', 'clickCount': 1}, session=sid)
            c.call('Input.dispatchMouseEvent', {'type': 'mouseReleased', 'x': p['x'], 'y': p['y'], 'button': 'left', 'clickCount': 1}, session=sid)
            sent = True
            break
        time.sleep(1)
    if not sent:
        c.call('Input.dispatchKeyEvent', {'type': 'keyDown', 'key': 'Enter', 'windowsVirtualKeyCode': 13}, session=sid)
        c.call('Input.dispatchKeyEvent', {'type': 'keyUp', 'key': 'Enter', 'windowsVirtualKeyCode': 13}, session=sid)
    time.sleep(3)

    return wait_reply(c, sid, cfg, timeout)


def wait_reply(c, sid, cfg, timeout=300):
    t0 = time.time()
    last, stable = '', 0
    while time.time() - t0 < timeout:
        body = c.ev(sid, 'document.body.innerText') or ''
        i = body.rfind(MARK)
        txt = body[i + len(MARK):] if i >= 0 else ''
        for cut in ('このパーソナリティは気に入りましたか', 'ChatGPT は間違えることがあります',
                    'Gemini は不正確な情報を表示することがあるため', '最新の応答'):
            j = txt.find(cut)
            if j > 0:
                txt = txt[:j]
        txt = txt.strip()
        busy = c.ev(sid, f'!!document.querySelector({json.dumps(cfg["busy"])})')
        if txt and txt == last and not busy:
            stable += 1
            if stable >= 3 and len(txt) > 150:
                return txt, None
        else:
            stable = 0
        last = txt
        time.sleep(4)
    return (last or None), 'タイムアウト'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('slug')
    ap.add_argument('--target', choices=['chatgpt', 'gemini', 'both'], default='both')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--timeout', type=int, default=360)
    a = ap.parse_args()

    slug_dir = ROOT / 'shorts' / a.slug
    data = json.loads((slug_dir / 'result.json').read_text(encoding='utf-8'))
    brief = ''
    bp = slug_dir / 'brief.yaml'
    if bp.exists():
        brief = bp.read_text(encoding='utf-8')
    prompt = build_prompt(a.slug, data, brief)

    if a.dry_run:
        print(prompt)
        return 0

    targets = ['chatgpt', 'gemini'] if a.target == 'both' else [a.target]
    c = C()
    rc = 0
    for tg in targets:
        print(f'[{tg}] 送信')
        try:
            reply, err = send(c, tg, prompt, a.timeout)
        except Exception as e:
            reply, err = None, f'{type(e).__name__}: {e}'
        if err:
            print(f'  !! {err}')
            rc = 1
        if reply:
            out = slug_dir / f'review_{tg}.md'
            out.write_text(reply + '\n', encoding='utf-8')
            print(f'  保存: {out} ({len(reply)} 文字)')
        time.sleep(2)
    c.ws.close()
    return rc


if __name__ == '__main__':
    sys.exit(main())


