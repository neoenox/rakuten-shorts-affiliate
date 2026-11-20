"""approve.py の回帰テスト（承認後検査・解決記録の入力検証）。"""
import importlib.util
import json
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'scripts'
sys.path.insert(0, str(SCRIPTS))


def load(name):
    path = SCRIPTS / f'{name}.py'
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'load failed: {path}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


approve = load('approve')


AFF = 'https://hb.afl.rakuten.co.jp/ichiba/xxxx.xxxx/?pc=https%3A%2F%2Fitem.rakuten.co.jp%2Fshop%2Fitem%2F'


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def make_project(tmp_path, *, needs=None, ver_status='pending', resolved=None):
    sd = tmp_path / 'shorts' / 'demo'
    result = {
        'title': '電気代の判断メモ', 'hook': 'フック', 'duration_sec': 35.0,
        'status': 'needs_review', 'scenes': [], 'claims': [],
        'needs_research': needs or [],
    }
    write(sd / 'result.json', result)
    write(sd / 'render.json', {
        'product_name': '電源タップ', 'affiliate': {'url': AFF},
    })
    write(sd / 'verification.json', {
        'slug': 'demo', 'status': ver_status, 'approved_by': 'owner',
        'approved_at': '2026-11-19T10:00:00+09:00',
        'expires_at': (date.today() + timedelta(days=14)).isoformat(),
        'result_sha256': approve.gate.sha256_file(sd / 'result.json'),
        'failures': [], 'resolved_needs': resolved or [],
        'checks': {k: {'passed': True} for k in approve.MANUAL_KEYS},
    })
    return sd


def test_sign_rejects_when_ready_recheck_fails(tmp_path, monkeypatch):
    """status 変更後の形式検査が失敗したら ready にしない。"""
    sd = make_project(tmp_path)
    monkeypatch.setattr(approve, 'ROOT', tmp_path)
    monkeypatch.setattr(approve, 'check_format', lambda path: (False, ['claims が空']))

    with pytest.raises(SystemExit, match='形式検査'):
        approve.sign('demo', by='owner')

    assert json.loads((sd / 'result.json').read_text(encoding='utf-8'))['status'] == 'needs_review'
    assert json.loads((sd / 'verification.json').read_text(encoding='utf-8'))['status'] == 'pending'


def test_sign_marks_ready_when_recheck_passes(tmp_path, monkeypatch):
    sd = make_project(tmp_path)
    monkeypatch.setattr(approve, 'ROOT', tmp_path)
    monkeypatch.setattr(approve, 'check_format', lambda path: (True, []))

    assert approve.sign('demo', by='owner') == 0

    result = json.loads((sd / 'result.json').read_text(encoding='utf-8'))
    ver = json.loads((sd / 'verification.json').read_text(encoding='utf-8'))
    assert result['status'] == 'ready'
    assert ver['status'] == 'approved'
    assert ver['result_sha256'] == approve.gate.sha256_file(sd / 'result.json')


def test_parse_resolves_rejects_non_numeric_index():
    with pytest.raises(SystemExit, match='整数'):
        approve.parse_resolves(['abc=解決した'], 1)


def test_parse_resolves_rejects_out_of_range_index():
    with pytest.raises(SystemExit, match='範囲外'):
        approve.parse_resolves(['2=解決した'], 1)


def test_parse_resolves_returns_indexed_text():
    assert approve.parse_resolves(['1=出典を確認した'], 1) == {1: '出典を確認した'}
