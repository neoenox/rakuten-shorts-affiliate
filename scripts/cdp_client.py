"""生CDP（WebSocket）の共通クライアント。

Playwright の connect_over_cdp が不安定なため、各スクリプトは Target.attachToTarget +
Runtime.evaluate を直接使う。接続・RPC・実クリックの共通部分をここに置き、
スクリプト固有の操作だけを各ファイルに残す。
"""
import json

import requests
import websocket


class Client:
    """Chrome の CDP WebSocket に接続し、id でレスポンスを待つ最小クライアント。"""

    def __init__(self, port=9222, ws_timeout=30, call_timeout=None):
        v = requests.get(f'http://127.0.0.1:{port}/json/version', timeout=10).json()
        self.ws = websocket.create_connection(v['webSocketDebuggerUrl'], timeout=ws_timeout)
        self.n = 0
        self.call_timeout = call_timeout

    def call(self, method, params=None, session=None, timeout=None):
        self.n += 1
        msg = {'id': self.n, 'method': method, 'params': params or {}}
        if session:
            msg['sessionId'] = session
        t = self.call_timeout if timeout is None else timeout
        if t is not None:
            self.ws.settimeout(t)
        self.ws.send(json.dumps(msg))
        while True:
            r = json.loads(self.ws.recv())
            if r.get('id') == self.n:
                return r

    def ev(self, sid, expr, timeout=None):
        r = self.call('Runtime.evaluate',
                      {'expression': expr, 'returnByValue': True, 'awaitPromise': True},
                      session=sid, timeout=timeout)
        return r.get('result', {}).get('result', {}).get('value')

    def pages(self):
        return [t for t in self.call('Target.getTargets')['result']['targetInfos']
                if t.get('type') == 'page']

    def page(self, match=''):
        cands = [t for t in self.pages() if match in (t.get('url') or '')]
        return cands[-1] if cands else None

    def attach(self, target_id):
        return self.call('Target.attachToTarget',
                         {'targetId': target_id, 'flatten': True})['result']['sessionId']

    def open(self, url, match):
        """一致するタブを再利用し、無ければ開いてセッションを返す。"""
        t = [x for x in self.pages() if match in (x.get('url') or '')]
        if t:
            tid = t[-1]['targetId']
        else:
            tid = self.call('Target.createTarget', {'url': url})['result']['targetId']
        sid = self.call('Target.attachToTarget', {'targetId': tid, 'flatten': True})['result']['sessionId']
        self.call('Target.activateTarget', {'targetId': tid})
        return sid

    def rclick(self, sid, x, y):
        self.call('Input.dispatchMouseEvent', {'type': 'mouseMoved', 'x': x, 'y': y}, session=sid)
        self.call('Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': x, 'y': y,
                                               'button': 'left', 'clickCount': 1}, session=sid)
        self.call('Input.dispatchMouseEvent', {'type': 'mouseReleased', 'x': x, 'y': y,
                                               'button': 'left', 'clickCount': 1}, session=sid)

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass
