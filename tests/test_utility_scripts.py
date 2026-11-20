"""小さなユーティリティの回帰テスト（パス展開・引数・seed保存）。"""
import importlib.util
import json
import sys
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


chrome = load('chrome_launch')
regen = load('regen_text')
freevideo = load('gen_freevideo')


def test_expand_user_data_dir(monkeypatch):
    monkeypatch.setenv('USERPROFILE', r'C:\Users\test')

    assert chrome.expand_user_data_dir(r'%USERPROFILE%\.chrome-gemienox') == r'C:\Users\test\.chrome-gemienox'


def test_regen_text_requires_slug(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['regen_text.py'])

    with pytest.raises(SystemExit) as exc:
        regen.main()

    assert exc.value.code == 2


def test_gen_freevideo_persists_generated_seed(tmp_path):
    spec_path = tmp_path / 'clips.json'
    spec = {'clips': [{'name': 'c1', 'prompt': 'x', 'seconds': 7.0}]}
    spec_path.write_text(json.dumps(spec), encoding='utf-8')

    seed = freevideo.resolve_seed(spec['clips'][0])
    spec['clips'][0]['seed'] = seed
    freevideo.save_spec(spec_path, spec)

    saved = json.loads(spec_path.read_text(encoding='utf-8'))
    assert saved['clips'][0]['seed'] == seed
