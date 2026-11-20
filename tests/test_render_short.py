"""render_short.py の回帰テスト（PR表示・尺設計・クリップキャッシュ・表記）。"""
import importlib.util
import os
import sys
from pathlib import Path

import pytest
from PIL import Image

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


R = load('render_short')


def script(**overrides):
    base = {
        'title': '電気代の判断メモ', 'hook': '電気代は下がる？',
        'duration_sec': 35.0, 'status': 'needs_review',
        'scenes': [{'start': 0.0, 'end': 5.0, 'narration': 'ナレーション',
                    'caption': ['テロップ'], 'visual': '模式図の説明',
                    'claim_ids': []}],
        'claims': [], 'needs_research': [],
    }
    base.update(overrides)
    return base


draw_calls = []


class FakeDraw:
    def __init__(self, im, mode='RGBA'):
        pass

    def rounded_rectangle(self, box, radius, fill=None, outline=None, width=1):
        draw_calls.append(('rect', box, fill, outline, width))

    def text(self, *a, **kw):
        pass

    def line(self, *a, **kw):
        pass

    def textlength(self, text, font=None):
        return 10.0


def test_caption_alpha_fades_only_at_scene_start():
    assert R.caption_alpha(0.0, 2.0) == 0.0
    assert R.caption_alpha(2.1, 2.0) == pytest.approx(0.1 / 0.22)
    assert R.caption_alpha(2.22, 2.0) == 1.0
    assert R.caption_alpha(10.0, 2.0) == 1.0


def test_pr_badge_is_full_alpha_while_caption_fades(monkeypatch):
    draw_calls.clear()
    monkeypatch.setattr(R.ImageDraw, 'Draw', FakeDraw)
    monkeypatch.setattr(R, 'font', lambda size, weight=600: object())

    R.draw_chrome(Image.new('RGB', (R.W, R.H)), script(), script()['scenes'][0], {},
                  0, 'ai', caption_alpha=0.0)

    pr = [c for c in draw_calls if c[0] == 'rect' and c[1] == (40, 96, 158, 168)]
    assert len(pr) == 1
    assert pr[0][2][-1] == 150


def test_plan_timing_pads_short_scenes_into_standard_range():
    starts, spans, total = R.plan_timing([1.0] * 5)

    assert starts[0] == 0.0
    assert all(3.0 <= s <= 9.0 for s in spans)
    assert 30.0 <= total <= 45.0


def test_plan_timing_rejects_overlong_narration():
    with pytest.raises(SystemExit, match='45秒'):
        R.plan_timing([9.0] * 5)


def test_clip_cache_dir_changes_when_source_changes(tmp_path):
    src = tmp_path / 'clip.mp4'
    src.write_bytes(b'a')
    other = tmp_path / 'other.mp4'
    other.write_bytes(b'a' * 100)
    os.utime(src, (1_000_000, 1_000_000))
    os.utime(other, (1_000_001, 1_000_001))

    a = R.clip_cache_dir(tmp_path / 'work', 'c1', src, 90)
    b = R.clip_cache_dir(tmp_path / 'work', 'c1', other, 90)

    assert a != b
    assert R.clip_cache_dir(tmp_path / 'work', 'c1', src, 90) == a


def test_description_discloses_real_footage_when_used():
    conf = {'art_types': {'1': 'photo'}}

    text = R.description(script(), conf)

    assert '実写' in text
