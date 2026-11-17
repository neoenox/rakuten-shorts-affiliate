"""生のCDP（ブラウザWebSocket直結）でStudioのページを操作する。

Playwright の connect_over_cdp がこの環境で不安定なため、Target.attachToTarget +
Runtime.evaluate を直接使う。usage:
  python scripts/cdp_raw.py "expr" --match videos/upload
"""
import argparse
import json
import sys
import time

import requests
import websocket

CDP = 'http://127.0.0.1:9222'


class Raw:
    def __init__(self):
        v = requests.get(CDP + '/json/version', timeout=10).json()
        self.ws = websocket.create_connection(v['webSocketDebuggerUrl'], timeout=90)
        self.n = 0

    def call(self, method, params=None, session=None, timeout=90):
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

    def pages(self):
        tg = self.call('Target.getTargets')['result']['targetInfos']
        return [t for t in tg if t.get('type') == 'page']

    def page(self, match=''):
        cands = [t for t in self.pages() if match in (t.get('url') or '')]
        return cands[-1] if cands else None

    def attach(self, target_id):
        return self.call('Target.attachToTarget', {'targetId': target_id, 'flatten': True})['result']['sessionId']

    def eval(self, session, expr, await_promise=False, timeout=90):
        r = self.call('Runtime.evaluate',
                      {'expression': expr, 'returnByValue': True, 'awaitPromise': await_promise},
                      session=session, timeout=timeout)
        res = r.get('result', {})
        if 'exceptionDetails' in res:
            return {'__exc__': json.dumps(res['exceptionDetails'], ensure_ascii=False)[:300]}
        return res.get('result', {}).get('value')

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('expr')
    ap.add_argument('--match', default='studio.youtube.com')
    ap.add_argument('--await', action='store_true')
    a = ap.parse_args()
    raw = Raw()
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
