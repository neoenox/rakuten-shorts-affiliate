"""shorts_standard.py の回帰テスト（形式検査の成否と追加規則）。"""
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

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


S = load('shorts_standard')


def data(**overrides):
    base = {
        'title': '電気代の判断メモ',
        'hook': '電気代は本当に下がる？',
        'duration_sec': 35.0,
        'status': 'needs_review',
        'scenes': [{
            'start': 0.0, 'end': 5.0,
            'narration': 'まず結論から言うと、確認してみる価値はあります。',
            'caption': ['確認する価値', 'はある'],
            'visual': '模式図：電力の流れを矢印で示す',
            'claim_ids': [],
        }],
        'claims': [],
        'needs_research': [],
    }
    base.update(overrides)
    return base


def test_cmd_check_fails_when_validator_failed_silently(tmp_path, monkeypatch):
    """validate.py が非0なのに出力が空でも、check コマンドは成功させない。"""
    p = tmp_path / 'result.json'
    p.write_text('{}', encoding='utf-8')
    monkeypatch.setattr(S, 'check', lambda path: (False, []))

    rc = S.cmd_check(SimpleNamespace(result=str(p)))

    assert rc == 1


def test_cmd_to_spec_fails_when_validator_failed_silently(tmp_path, monkeypatch):
    p = tmp_path / 'result.json'
    p.write_text(json.dumps(data(status='ready')), encoding='utf-8')
    monkeypatch.setattr(S, 'check', lambda path: (False, []))

    rc = S.cmd_to_spec(SimpleNamespace(result=str(p), slug='demo', art=None, pron=None,
                                       out=str(tmp_path / 'short_spec.json'),
                                       long_id=None, long_title=None, credit=None, art_map=None))

    assert rc == 1


def test_extra_checks_ready_without_claims_is_error():
    issues = S.extra_checks(data(status='ready'))

    assert any(lv == 'ERROR' and 'claims' in msg for lv, msg in issues)


def test_brief_check_requires_sources_and_facts(tmp_path):
    p = tmp_path / 'brief.yaml'
    p.write_text(
        'topic: 電気代\nviewer_question: どうすれば下がる？\naudience: 一般\n'
        'visual_assets: 模式図\nsource_urls:\n  - https://example.test/\n'
        'verified_facts:\n  - 事実\ncaveats:\n  - 特になし\n',
        encoding='utf-8')

    assert S.brief_check(p) == []
