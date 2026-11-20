"""upload_short.py の回帰テスト（file input 選択）。"""
import importlib.util
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


upload = load('upload_short')


def test_video_input_rejects_image_only_inputs():
    with pytest.raises(SystemExit, match='動画用'):
        upload.video_input([{'nodeId': 1, 'accept': 'image/*'}])


def test_video_input_selects_video_input():
    files = [{'nodeId': 1, 'accept': 'image/*'}, {'nodeId': 2, 'accept': 'video/*'}]

    assert upload.video_input(files)['nodeId'] == 2
