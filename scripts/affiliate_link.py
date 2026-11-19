"""楽天の商品URLからアフィリエイトリンク（hb.afl）を作る。生CDP。

usage:
  python scripts/affiliate_link.py <商品URL> [<商品URL> ...]
  python scripts/affiliate_link.py --json urls.json     # [{"slug":..., "url":...}, ...]

出力: 商品URL -> hb.afl のテキストリンク（link_type と ut を落とした素の形）
"""
import argparse
import json
import re
import sys
import time
import urllib.parse
from pathlib import Path

from cdp_client import Client

ROOT = Path(__file__).resolve().parents[1]


def make_link(c, product_url):
    """freelink を開いて hb.afl のURLを取り出す。"""
    if c:
        c.ws.close()
    c = Client(ws_timeout=120, call_timeout=90)
    q = urllib.parse.quote(product_url, safe='')
    tid = c.call('Target.createTarget', {'url': f'https://affiliate.rakuten.co.jp/freelink?u={q}'})['result']['targetId']
    sid = c.call('Target.attachToTarget', {'targetId': tid, 'flatten': True})['result']['sessionId']
    c.call('Target.activateTarget', {'targetId': tid})

    # リンク作成ページの #codebox にURLが入る。空なら「リンクのみ」を選んで待つ。
    found = None
    clicked = False
    for i in range(40):
        time.sleep(2)
        val = c.ev(sid, "(document.querySelector('#codebox') || {value:''}).value") or ''
        if 'hb.afl.rakuten.co.jp' in val:
            found = val.strip()
            break
        if not clicked and i >= 3 and 'リンクのみ' in (c.ev(sid, 'document.body.innerText') or ''):
            c.ev(sid, """(() => { const els = Array.from(document.querySelectorAll('label, button, a, span, div'));
              const t = els.find(e => (e.textContent || '').trim() === 'リンクのみ' && e.getBoundingClientRect().width > 0);
              if (t) { t.click(); return true; } return false; })()""")
            clicked = True
    c.call('Target.closeTarget', {'targetId': tid})
    c.ws.close()
    if not found:
        return None
    # 画像付きHTMLが返ることがあるので、最初の ?pc= だけを取り出す
    m = re.search(r'https://hb\.afl\.rakuten\.co\.jp/ichiba/[^/\s"]+/\?pc=[^&\s"]+', found)
    if m:
        return m.group(0)
    base, _, query = found.partition('?')
    keep = [kv for kv in query.split('&') if kv.startswith('pc=')]
    return base + ('?' + '&'.join(keep) if keep else '')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('urls', nargs='*')
    ap.add_argument('--json')
    a = ap.parse_args()

    targets = []
    if a.json:
        for item in json.loads(Path(a.json).read_text(encoding='utf-8')):
            targets.append((item.get('slug', ''), item['url']))
    for u in a.urls:
        targets.append(('', u))

    out = {}
    c = None
    for slug, u in targets:
        link = make_link(c, u)
        print(json.dumps({'slug': slug, 'product': u, 'affiliate': link}, ensure_ascii=False))
        out[slug or u] = link
    if a.json:
        Path(a.json).with_suffix('.links.json').write_text(
            json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
        print('written:', Path(a.json).with_suffix('.links.json'), file=sys.stderr)


if __name__ == '__main__':
    main()


