"""楽天アフィリエイトにサイトを1件登録する。

usage: python scripts/rakuten_add_site.py "<サイト名>" "<URL>" [--genre 30] [--priority 3]

前提: 分離Chrome（9222）で楽天アフィリエイトにログイン済み。
"""
import argparse
import json
import sys
import time

import requests
import websocket

CDP = 'http://127.0.0.1:9222'


class C:
    def __init__(self):
        v = requests.get(CDP + '/json/version', timeout=10).json()
        self.ws = websocket.create_connection(v['webSocketDebuggerUrl'], timeout=120)
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

    def ev(self, sid, expr, timeout=90):
        r = self.call('Runtime.evaluate', {'expression': expr, 'returnByValue': True, 'awaitPromise': True},
                      session=sid, timeout=timeout)
        return r.get('result', {}).get('result', {}).get('value')

    def open(self, url, match='/user/sites'):
        pages = [t for t in self.call('Target.getTargets')['result']['targetInfos'] if t.get('type') == 'page']
        t = [x for x in pages if match in (x.get('url') or '')]
        tid = t[-1]['targetId'] if t else self.call('Target.createTarget', {'url': url})['result']['targetId']
        sid = self.call('Target.attachToTarget', {'targetId': tid, 'flatten': True})['result']['sessionId']
        self.call('Target.activateTarget', {'targetId': tid})
        return sid

    def viewport(self, sid, width, height):
        """縦長のビューポートにする。入力欄やボタンが画面外だと実クリックが外れるため。"""
        self.call('Emulation.setDeviceMetricsOverride',
                  {'width': width, 'height': height, 'deviceScaleFactor': 1, 'mobile': False}, session=sid)

    def clear_viewport(self, sid):
        self.call('Emulation.clearDeviceMetricsOverride', session=sid)

    def rclick(self, sid, x, y):
        self.call('Input.dispatchMouseEvent', {'type': 'mouseMoved', 'x': x, 'y': y}, session=sid)
        self.call('Input.dispatchMouseEvent', {'type': 'mousePressed', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1}, session=sid)
        self.call('Input.dispatchMouseEvent', {'type': 'mouseReleased', 'x': x, 'y': y, 'button': 'left', 'clickCount': 1}, session=sid)


def button_point(c, sid, label):
    """ラベルの一致するボタンの中心座標を返す。画面外なら縦長にして収める。

    `main` のスクロール領域は window ではないため、scrollIntoView だけでは
    ビューポート内に入らない（2026-11-19 実測）。
    """
    js = """(() => {
      const b = Array.from(document.querySelectorAll('button'))
        .find(x => (x.innerText || '').trim() === %s && x.getBoundingClientRect().width > 0);
      if (!b) return null;
      b.scrollIntoView({block: 'center'});
      const r = b.getBoundingClientRect();
      return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2),
              vw: innerWidth, vh: innerHeight};
    })()""" % json.dumps(label)
    pt = c.ev(sid, js)
    if pt and 0 <= pt['y'] < pt['vh']:
        return pt
    if not pt:
        return None
    c.viewport(sid, max(1000, pt['vw']), pt['y'] + 120)
    time.sleep(1)
    pt = c.ev(sid, js)
    if not pt or not (0 <= pt['y'] < pt['vh']):
        return None
    return pt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('name')
    ap.add_argument('url')
    ap.add_argument('--genre', default='30')      # 住まい・インテリア・雑貨
    ap.add_argument('--priority', default='3')
    a = ap.parse_args()

    c = C()
    sid = c.open('https://affiliate.rakuten.co.jp/user/sites/create', '/user/sites/create')
    for _ in range(30):
        if c.ev(sid, "!!document.querySelector('#site_name')"):
            break
        time.sleep(2)
    time.sleep(2)

    filled = c.ev(sid, """(() => {
      function set(el, val) {
        const d = Object.getOwnPropertyDescriptor(el.constructor.prototype, 'value');
        if (d && d.set) d.set.call(el, val); else el.value = val;
        el.dispatchEvent(new Event('input', {bubbles:true}));
        el.dispatchEvent(new Event('change', {bubbles:true}));
      }
      const n = document.querySelector('#site_name');
      const u = document.querySelector('#site_url');
      const p = document.querySelector('select[name=priority]');
      const g = document.querySelector('select[name=genre]');
      if (!n || !u) return {ok: false};
      set(n, %s); set(u, %s);
      if (p) set(p, %s);
      if (g) set(g, %s);
      return {ok: true, name: n.value, url: u.value, pri: p ? p.value : null, gen: g ? g.value : null};
    })()""" % (json.dumps(a.name), json.dumps(a.url), json.dumps(a.priority), json.dumps(a.genre)))
    print('入力:', json.dumps(filled, ensure_ascii=False))
    time.sleep(2)

    btn = button_point(c, sid, 'サイト情報を登録する')
    print('登録ボタン:', btn)
    if not btn:
        return 1
    c.rclick(sid, btn['x'], btn['y'])
    c.clear_viewport(sid)
    time.sleep(8)

    out = c.ev(sid, "document.body.innerText") or ''
    print('URL:', c.ev(sid, 'location.href.slice(0, 70)'))
    print('一覧に反映:', a.url.rstrip('/') in out or a.name in out)
    c.ws.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
