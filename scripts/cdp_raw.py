"""生のCDP（ブラウザWebSocket直結）でStudioのページを操作する。

Playwright の connect_over_cdp がこの環境で不安定なため、Target.attachToTarget +
Runtime.evaluate を直接使う。usage:
  python scripts/cdp_raw.py "expr" --match videos/upload
"""
import argparse
import json
import sys

from cdp_client import Client


class Raw(Client):
    def __init__(self, port=9222):
        super().__init__(port=port, ws_timeout=90, call_timeout=90)

    def eval(self, session, expr, await_promise=False, timeout=90):
        r = self.call('Runtime.evaluate',
                      {'expression': expr, 'returnByValue': True, 'awaitPromise': await_promise},
                      session=session, timeout=timeout)
        res = r.get('result', {})
        if 'exceptionDetails' in res:
            return {'__exc__': json.dumps(res['exceptionDetails'], ensure_ascii=False)[:300]}
        return res.get('result', {}).get('value')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('expr')
    ap.add_argument('--match', default='studio.youtube.com')
    ap.add_argument('--port', type=int, default=9222)
    ap.add_argument('--await', action='store_true')
    a = ap.parse_args()
    raw = Raw(a.port)
    try:
        t = raw.page(a.match) or raw.page()
        if not t:
            print('no page target', file=sys.stderr)
            return 1
        sid = raw.attach(t['targetId'])
        val = raw.eval(sid, a.expr, await_promise=getattr(a, 'await'))
        print(json.dumps(val, ensure_ascii=False, indent=1))
        return 0
    finally:
        raw.close()


if __name__ == '__main__':
    sys.exit(main())
