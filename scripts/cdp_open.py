"""CDP で新しいタブを開く（生CDP・Playwright不使用）。

usage:
  python scripts/cdp_open.py https://affiliate.rakuten.co.jp/
  python scripts/cdp_open.py <url> --same      # 既存タブを使い回す
"""
import argparse
import json
import time

import requests
import websocket

CDP = 'http://127.0.0.1:9222'


def connect():
    v = requests.get(CDP + '/json/version', timeout=10).json()
    ws = websocket.create_connection(v['webSocketDebuggerUrl'], timeout=30)
    n = [0]

    def call(method, params=None, session=None, timeout=45):
        n[0] += 1
        msg = {'id': n[0], 'method': method, 'params': params or {}}
        if session:
            msg['sessionId'] = session
        ws.settimeout(timeout)
        ws.send(json.dumps(msg))
        while True:
            r = json.loads(ws.recv())
            if r.get('id') == n[0]:
                return r

    return ws, call


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('url')
    ap.add_argument('--same', action='store_true', help='既存のタブをこのURLへ移動する')
    a = ap.parse_args()

    ws, call = connect()
    try:
        if a.same:
            pages = [t for t in call('Target.getTargets')['result']['targetInfos'] if t.get('type') == 'page']
            target = pages[-1]
            sid = call('Target.attachToTarget', {'targetId': target['targetId'], 'flatten': True})['result']['sessionId']
            call('Page.navigate', {'url': a.url}, session=sid)
            call('Target.activateTarget', {'targetId': target['targetId']})
            print('navigated:', a.url)
        else:
            tid = call('Target.createTarget', {'url': a.url})['result']['targetId']
            call('Target.activateTarget', {'targetId': tid})
            print('opened:', a.url, 'target:', tid[:12])
        time.sleep(3)
    finally:
        ws.close()


if __name__ == '__main__':
    main()
