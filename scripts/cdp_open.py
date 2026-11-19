"""CDP で新しいタブを開く（生CDP・Playwright不使用）。

usage:
  python scripts/cdp_open.py https://affiliate.rakuten.co.jp/
  python scripts/cdp_open.py <url> --same      # 既存タブを使い回す
"""
import argparse
import time

from cdp_client import Client


def connect():
    c = Client(ws_timeout=30, call_timeout=45)
    return c.ws, c.call


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
