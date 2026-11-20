"""render_yorimichi.py の回帰テスト（spec変換・描画・説明欄）。"""
import importlib.util
import sys
from pathlib import Path

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


Y = load('render_yorimichi')
R = load('render_short')


def spec():
    return {
        'title': '節電すべき時間', 'hook': 'いつ電気を使う？',
        'notes': '・出典\n  https://example.test/', 'refs': ['出典 — https://example.test/'],
        'status': 'needs_review',
        'claims': [{'id': 'c1', 'statement': '数値', 'source_url': 'https://example.test/'}],
        'scenes': [
            {'text': 'まず結論です', 'big': '結論', 'sub': '夜',
             'art': 'assets/demo/bg.png'},
        ],
        'art': 'assets/demo/bg.png', 'hashtags': '#Shorts',
    }


draw_calls = []


class FakeDraw:
    def __init__(self, im, mode='RGBA'):
        pass

    def text(self, xy, text, **kw):
        draw_calls.append(('text', xy, text, kw.get('fill')))

    def line(self, *a, **kw):
        draw_calls.append(('line', a, kw.get('fill')))

    def rounded_rectangle(self, box, radius, **kw):
        draw_calls.append(('rect', box, kw.get('fill')))

    def rectangle(self, box, **kw):
        draw_calls.append(('rect', box, kw.get('fill')))

    def textlength(self, text, font=None):
        return 10.0


def test_spec_to_data_maps_scenes_and_claims():
    data = Y.spec_to_data(spec())

    assert data['scenes'][0]['narration'] == 'まず結論です'
    assert data['scenes'][0]['caption'] == ['結論', '夜']
    assert data['claims'][0]['id'] == 'c1'


def test_merge_evidence_keeps_claim_ids_from_result():
    data = Y.spec_to_data(spec())
    result = {'scenes': [{'claim_ids': ['c1'], 'visual': '模式図の説明'}]}

    Y.merge_evidence(data, result)

    assert data['scenes'][0]['claim_ids'] == ['c1']
    assert data['scenes'][0]['visual'] == '模式図の説明'


def test_pr_and_type_label_stay_opaque_during_caption_fade(monkeypatch):
    draw_calls.clear()
    monkeypatch.setattr(R.ImageDraw, 'Draw', FakeDraw)
    monkeypatch.setattr(R, 'font', lambda size, weight=600: object())
    data = Y.spec_to_data(spec())
    Y.merge_evidence(data, {'scenes': [{'claim_ids': [], 'visual': ''}]})

    Y.draw_frame(Image.new('RGB', (R.W, R.H)), data['scenes'][0], data,
                 {'art_types': {'1': 'ai'}}, 1, 0.0, 0.0, 5.0, 'ai', caption_alpha=0.0)

    rects = [c for c in draw_calls if c[0] == 'rect']
    assert any(c[1] == (40, 96, 158, 168) and c[2] and c[2][-1] == 150 for c in rects)
    assert any(c[2] and c[2][-1] == 140 for c in rects)


def test_description_keeps_affiliate_and_pr():
    data = Y.spec_to_data(spec())
    conf = {
        'product_name': '電源タップ',
        'affiliate': {'url': 'https://hb.afl.rakuten.co.jp/x'},
    }

    text = Y.description(data, conf)

    assert text.startswith('【PR】')
    assert '電源タップ' in text
    assert 'https://hb.afl.rakuten.co.jp/x' in text
    assert 'AI生成' in text
