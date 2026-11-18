"""gate.py の回帰テスト（承認の失効・期限・表記・リンク形式）。

ネットワークと ffmpeg は使わない（network=False / fingerprints=False / run_format=False）。
"""
import json
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import gate  # noqa: E402

AFF = 'https://hb.afl.rakuten.co.jp/ichiba/xxxx.xxxx/?pc=https%3A%2F%2Fitem.rakuten.co.jp%2Fshop%2Fitem%2F'
TITLE = '電気ポットの保温、年3,330円'
PRODUCT = 'MAXZEN 電気ケトル 1.0L（保温なし・空だき防止）'


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def desc_text():
    return (f'【PR】この動画は楽天アフィリエイト（アフィリエイト広告）を含みます。\n'
            f'商品名：{PRODUCT}\n{AFF}\n\n{TITLE}\n\n'
            '■ 映像と音声について\n・映像はAI生成のイメージ、自作のイラスト・模式図です。\n')


def comment_text():
    return (f'【PR】この動画はアフィリエイト広告を含みます。\n{TITLE}\n'
            f'商品名：{PRODUCT}\n商品ページ：{AFF}\n'
            '映像はAI生成のイメージ、自作のイラスト・模式図です。\n')


def make_project(tmp_path, *, status='ready', needs=None, ver='approved',
                 expires=None, approved_by='owner', touch_result_after=False,
                 desc=None, comment=None):
    sd = tmp_path / 'shorts' / 'demo'
    result = {
        'title': TITLE, 'hook': 'フック', 'duration_sec': 35.0, 'status': status,
        'scenes': [], 'claims': [], 'needs_research': needs or [],
    }
    write(sd / 'result.json', result)
    write(sd / 'render.json', {
        'speaker': '青山龍星', 'product_name': PRODUCT, 'affiliate': {'url': AFF},
    })
    (tmp_path / 'scripts').mkdir(parents=True, exist_ok=True)

    out = tmp_path / 'out'
    out.mkdir()
    (out / 'demo.mp4').write_bytes(b'video')
    (out / 'demo_thumb.jpg').write_bytes(b'thumb')
    (out / 'demo_description.md').write_text(desc if desc is not None else desc_text(), encoding='utf-8')
    (out / 'demo_fixed_comment.md').write_text(comment if comment is not None else comment_text(), encoding='utf-8')

    if ver is not None:
        v = {
            'slug': 'demo', 'status': ver, 'approved_by': approved_by,
            'approved_at': '2026-11-19T10:00:00+09:00',
            'expires_at': expires or (date.today() + timedelta(days=14)).isoformat(),
            'result_sha256': gate.sha256_file(sd / 'result.json'),
            'checks': {}, 'failures': [], 'artifacts': {},
        }
        write(sd / 'verification.json', v)

    if touch_result_after:
        r = gate.load_json(sd / 'result.json')
        r['hook'] = '承認後に書き換えた'
        write(sd / 'result.json', r)
    return sd


def run(tmp_path):
    return gate.evaluate('demo', root=tmp_path, network=False,
                         fingerprints=False, run_format=False)


def test_valid_state_passes(tmp_path):
    make_project(tmp_path)
    info = run(tmp_path)
    assert info['passed'], info['failures']


def test_needs_research_blocks(tmp_path):
    make_project(tmp_path, needs=['商品リンクを作る'])
    info = run(tmp_path)
    assert not info['passed']
    assert any('needs_research' in f for f in info['failures'])


def test_not_ready_blocks(tmp_path):
    make_project(tmp_path, status='needs_review')
    info = run(tmp_path)
    assert not info['passed']
    assert any('status' in f for f in info['failures'])


def test_missing_verification_blocks(tmp_path):
    make_project(tmp_path, ver=None)
    info = run(tmp_path)
    assert not info['passed']
    assert any('verification.json' in f for f in info['failures'])


def test_pending_verification_blocks(tmp_path):
    make_project(tmp_path, ver='pending')
    info = run(tmp_path)
    assert not info['passed']
    assert any('approved' in f for f in info['failures'])


def test_expired_approval_blocks(tmp_path):
    make_project(tmp_path, expires=(date.today() - timedelta(days=1)).isoformat())
    info = run(tmp_path)
    assert not info['passed']
    assert any('期限' in f for f in info['failures'])


def test_result_change_invalidates_approval(tmp_path):
    make_project(tmp_path, touch_result_after=True)
    info = run(tmp_path)
    assert not info['passed']
    assert any('SHA-256' in f for f in info['failures'])


def test_presentation_requires_pr(tmp_path):
    make_project(tmp_path, desc='PR表記なし\n' + desc_text()[4:])
    info = run(tmp_path)
    assert not info['passed']
    assert any('【PR】' in f for f in info['failures'])


def test_presentation_requires_product_and_link(tmp_path):
    text = comment_text().replace(PRODUCT, '別の商品')
    make_project(tmp_path, comment=text)
    info = run(tmp_path)
    assert not info['passed']
    assert any('商品名' in f for f in info['failures'])


def test_link_url_format():
    assert gate.check_link_url(AFF) is None
    assert gate.check_link_url('https://example.com/x') is not None
    assert gate.check_link_url('ftp://hb.afl.rakuten.co.jp/x') is not None


@pytest.mark.parametrize('days,ok', [(0, True), (-1, False), (1, True)])
def test_is_expired_boundary(days, ok):
    d = (date.today() + timedelta(days=days)).isoformat()
    assert (not gate.is_expired(d)) is ok
