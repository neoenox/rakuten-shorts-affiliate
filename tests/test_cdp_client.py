"""共通 CDP クライアントの回帰テスト（実ブラウザ・ネットワークなし）。

各スクリプトが従来と同じタイムアウト・RPC・実クリックを維持していることを確認する。
"""
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'scripts'
sys.path.insert(0, str(SCRIPTS))


class FakeWS:
    def __init__(self, responses=None):
        self.sent = []
        self.timeouts = []
        self.responses = list(responses or [])
        self.closed = False

    def settimeout(self, seconds):
        self.timeouts.append(seconds)

    def send(self, text):
        self.sent.append(json.loads(text))

    def recv(self):
        if self.responses:
            return json.dumps(self.responses.pop(0))
        return json.dumps({'id': self.sent[-1]['id'], 'result': {}})

    def close(self):
        self.closed = True


@pytest.fixture
def fake_cdp(monkeypatch):
    ws = FakeWS()
    seen = {}

    def get(url, timeout):
        seen['url'] = url
        seen['get_timeout'] = timeout
        return SimpleNamespace(json=lambda: {'webSocketDebuggerUrl': 'ws://fake'})

    def connect(url, timeout):
        seen['ws_url'] = url
        seen['ws_timeout'] = timeout
        return ws

    monkeypatch.setattr(cdp_client.requests, 'get', get)
    monkeypatch.setattr(cdp_client.websocket, 'create_connection', connect)
    return ws, seen


def load(name, module_name=None):
    path = SCRIPTS / f'{name}.py'
    spec = importlib.util.spec_from_file_location(module_name or f'_cdp_test_{name}', path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'load failed: {path}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


cdp_client = load('cdp_client', 'cdp_client')


def test_call_waits_for_matching_id_and_sets_timeout(fake_cdp):
    ws, seen = fake_cdp
    ws.responses = [{'id': 99, 'result': {}}, {'id': 1, 'result': {'ok': True}}]
    c = cdp_client.Client(ws_timeout=30, call_timeout=45)

    assert c.call('Target.getTargets', {'depth': 1}, session='S') == {
        'id': 1, 'result': {'ok': True}}
    assert ws.sent == [{'id': 1, 'method': 'Target.getTargets',
                        'params': {'depth': 1}, 'sessionId': 'S'}]
    assert ws.timeouts == [45]
    assert seen['url'] == 'http://127.0.0.1:9222/json/version'
    assert seen['get_timeout'] == 10
    assert seen['ws_timeout'] == 30


def test_call_without_call_timeout_leaves_socket_timeout_alone(fake_cdp):
    ws, _ = fake_cdp
    cdp_client.Client().call('Target.getTargets')
    assert ws.timeouts == []


def test_ev_extracts_value(fake_cdp):
    ws, _ = fake_cdp
    ws.responses = [{'id': 1, 'result': {'result': {'value': {'title': 'x'}}}}]
    c = cdp_client.Client(call_timeout=90)

    assert c.ev('S', 'document.title') == {'title': 'x'}
    assert ws.sent[0]['method'] == 'Runtime.evaluate'
    assert ws.sent[0]['params'] == {'expression': 'document.title',
                                    'returnByValue': True, 'awaitPromise': True}
    assert ws.sent[0]['sessionId'] == 'S'


def test_rclick_sends_three_events_in_order(fake_cdp):
    ws, _ = fake_cdp
    cdp_client.Client(call_timeout=90).rclick('S', 10, 20)

    assert [(m['method'], m['params']['type']) for m in ws.sent] == [
        ('Input.dispatchMouseEvent', 'mouseMoved'),
        ('Input.dispatchMouseEvent', 'mousePressed'),
        ('Input.dispatchMouseEvent', 'mouseReleased'),
    ]
    assert all(m['params']['x'] == 10 and m['params']['y'] == 20
               and m['sessionId'] == 'S' for m in ws.sent)
    assert [m['params'].get('button') for m in ws.sent] == [None, 'left', 'left']
    assert [m['params'].get('clickCount') for m in ws.sent] == [None, 1, 1]


def test_open_reuses_matching_tab(fake_cdp):
    ws, _ = fake_cdp
    ws.responses = [
        {'id': 1, 'result': {'targetInfos': [
            {'type': 'background_page', 'url': 'https://a.test'},
            {'type': 'page', 'url': 'https://a.test/page', 'targetId': 'T'},
        ]}},
        {'id': 2, 'result': {'sessionId': 'S'}},
        {'id': 3, 'result': {}},
    ]
    c = cdp_client.Client(call_timeout=90)

    assert c.open('https://new.test', 'a.test') == 'S'
    assert [m['method'] for m in ws.sent] == [
        'Target.getTargets', 'Target.attachToTarget', 'Target.activateTarget']
    assert ws.sent[1]['params'] == {'targetId': 'T', 'flatten': True}


def test_open_creates_tab_when_no_match(fake_cdp):
    ws, _ = fake_cdp
    ws.responses = [
        {'id': 1, 'result': {'targetInfos': []}},
        {'id': 2, 'result': {'targetId': 'NEW'}},
        {'id': 3, 'result': {'sessionId': 'S'}},
        {'id': 4, 'result': {}},
    ]
    c = cdp_client.Client(call_timeout=90)

    assert c.open('https://new.test', 'a.test') == 'S'
    assert ws.sent[1]['method'] == 'Target.createTarget'
    assert ws.sent[1]['params'] == {'url': 'https://new.test'}


@pytest.mark.parametrize('name, factory, ws_timeout, call_timeout', [
    ('cdp_page', lambda m: m.Client(), 30, None),
    ('cdp_raw', lambda m: m.Raw(), 90, 90),
    ('rakuten_add_site', lambda m: m.C(), 120, 90),
    ('google_ai_review', lambda m: m.C(), 180, 120),
    ('script_review', lambda m: m.C(), 180, 120),
    ('upload_short', lambda m: m.CDP(), 180, 120),
])
def test_migrated_clients_keep_timeouts(fake_cdp, name, factory, ws_timeout, call_timeout):
    ws, seen = fake_cdp
    c = factory(load(name))

    c.call('Target.getTargets')
    assert seen['ws_timeout'] == ws_timeout
    assert ws.timeouts == ([] if call_timeout is None else [call_timeout])


def test_cdp_open_connect_keeps_timeouts(fake_cdp):
    ws, seen = fake_cdp
    ws2, call = load('cdp_open').connect()

    assert ws2 is ws
    call('Target.getTargets')
    assert seen['ws_timeout'] == 30
    assert ws.timeouts == [45]


def test_affiliate_link_creates_client_with_original_timeouts(fake_cdp, monkeypatch):
    ws, seen = fake_cdp
    mod = load('affiliate_link')
    ws.responses = [{'id': 1, 'result': {'targetId': 'T'}},
                    {'id': 2, 'result': {'sessionId': 'S'}}]
    monkeypatch.setattr(mod.time, 'sleep', lambda _: None)

    assert mod.make_link(None, 'https://example.test/item') is None
    assert seen['ws_timeout'] == 120
    assert ws.timeouts[0] == 90


@pytest.mark.parametrize('name, factory, method', [
    ('cdp_raw', lambda m: m.Raw(), 'eval'),
    ('script_review', lambda m: m.C(), 'ev'),
])
def test_exception_details_are_reported_as_before(fake_cdp, name, factory, method):
    ws, _ = fake_cdp
    ws.responses = [{'id': 1, 'result': {'exceptionDetails': {'text': 'boom'}}}]
    c = factory(load(name))

    out = getattr(c, method)('S', 'bad(')
    assert out == {'__exc__': json.dumps({'text': 'boom'}, ensure_ascii=False)[:300]}
