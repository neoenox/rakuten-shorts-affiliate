"""CDP（ブラウザの WebSocket）でページの JS を実行する。Playwright が不安定なときの代替。

usage:
  python scripts/cdp_page.py "document.title" --match videos/upload
  python scripts/cdp_page.py --list
"""
import argparse
import json
import sys

from cdp_client import Client


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('expr', nargs='?', default=None)
    ap.add_argument('--match', default='')
    ap.add_argument('--list', action='store_true')
    a = ap.parse_args()

    c = Client(ws_timeout=30)
    try:
        tg = c.call('Target.getTargets')['result']['targetInfos']
        pages = [t for t in tg if t.get('type') == 'page']
        if a.list or not a.expr:
            for t in pages:
                print(t.get('url', '')[:140])
            return 0

        cands = [t for t in pages if a.match and a.match in (t.get('url') or '')] or pages
        target = cands[-1]
        att = c.call('Target.attachToTarget', {'targetId': target['targetId'], 'flatten': True})
        sid = att['result']['sessionId']
        res = c.call('Runtime.evaluate', {'expression': a.expr, 'returnByValue': True, 'awaitPromise': True}, session=sid)
        r = res.get('result', {})
        if 'exceptionDetails' in r:
            print('EXCEPTION:', json.dumps(r['exceptionDetails'], ensure_ascii=False)[:400])
            return 1
        val = r.get('result', {})
        print(json.dumps(val.get('value'), ensure_ascii=False, indent=1))
        return 0
    finally:
        c.close()


if __name__ == '__main__':
    sys.exit(main())
