"""build_hub.py の回帰テスト（収集・検査・エスケープ・停止条件・リンク確認）。

ネットワークと GitHub は使わない。git は一時ディレクトリの bare リポジトリで完結させる。
"""
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_hub  # noqa: E402

AFF = 'https://hb.afl.rakuten.co.jp/ichiba/xxxx.xxxx/?pc=https%3A%2F%2Fitem.rakuten.co.jp%2Fshop%2Fitem%2F'
DAY = date(2026, 11, 19)


def item(slug, product='商品A', aff=AFF, title='動画', video_id='vid', published_at='2026-11-19'):
    return {'slug': slug, 'product': product, 'affiliate': aff, 'title': title,
            'video_id': video_id, 'published_at': published_at}


def git(*args, cwd=None):
    cp = subprocess.run(['git', *args], cwd=cwd, capture_output=True, text=True, encoding='utf-8')
    assert cp.returncode == 0, cp.stderr
    return cp.stdout


def init_repo(path):
    path.mkdir()
    git('init', '-b', 'main', cwd=path)
    git('config', 'user.name', 'test', cwd=path)
    git('config', 'user.email', 'test@example.com', cwd=path)
    return path


def commit_page(repo, items):
    (repo / 'index.html').write_text(build_hub.render(items, DAY), encoding='utf-8')
    git('add', 'index.html', cwd=repo)
    git('commit', '-m', 'initial', cwd=repo)


# --- collect ---

def write_short(root, slug, visibility='public', product='商品A', aff=AFF, published_at='2026-11-19'):
    d = root / slug
    d.mkdir(parents=True)
    (d / 'publish.json').write_text(
        '{"visibility": "%s", "title": "%s", "video_id": "v-%s", "published_at": "%s"}'
        % (visibility, slug, slug, published_at), encoding='utf-8')
    (d / 'render.json').write_text(
        '{"product_name": "%s", "affiliate": {"url": "%s"}}' % (product, aff), encoding='utf-8')


def test_collect_filters_and_sorts(tmp_path):
    write_short(tmp_path, 'old', published_at='2026-11-17')
    write_short(tmp_path, 'new', published_at='2026-11-19')
    write_short(tmp_path, 'hidden', visibility='held')
    items = build_hub.collect(tmp_path)
    assert [i['slug'] for i in items] == ['new', 'old']


def test_collect_skips_missing_product_or_link(tmp_path):
    write_short(tmp_path, 'ok')
    write_short(tmp_path, 'no_link', aff='')
    write_short(tmp_path, 'no_product', product='')
    items = build_hub.collect(tmp_path)
    assert [i['slug'] for i in items] == ['ok']


# --- check ---

def test_check_passes_for_clean_page():
    items = [item('a')]
    assert build_hub.check(build_hub.render(items, DAY), items) == []


@pytest.mark.parametrize('mutate, expected', [
    (lambda t: t.replace('アフィリエイト広告を含みます', ''), 'PR表記'),
    (lambda t: t.replace('<ul>', '<ul><img src="x">'), '画像'),
    (lambda t: t.replace('rel="nofollow sponsored noopener"', ''), 'rel="nofollow sponsored'),
])
def test_check_detects_violations(mutate, expected):
    items = [item('a')]
    text = mutate(build_hub.render(items, DAY))
    problems = build_hub.check(text, items)
    assert any(expected in p for p in problems)


def test_check_detects_price_in_product_and_missing_link():
    items = [item('a', product='商品 1,000円')]
    text = build_hub.render(items, DAY).replace(AFF, '')
    problems = build_hub.check(text, items)
    assert any('価格' in p for p in problems)
    assert any('リンクが無い' in p for p in problems)


def test_render_escapes_html():
    items = [item('a', product='A&B <b>')]
    text = build_hub.render(items, DAY)
    assert 'A&amp;B &lt;b&gt;' in text
    assert '<b>' not in text


# --- apply: 停止条件 ---

def test_apply_noop_leaves_repo_clean(tmp_path):
    items = [item('a')]
    repo = init_repo(tmp_path / 'repo')
    commit_page(repo, items)
    assert build_hub.apply(repo, build_hub.render(items, DAY), items) == 0
    assert git('status', '--porcelain', cwd=repo).strip() == ''


def test_apply_blocks_card_decrease(tmp_path):
    old = [item('a'), item('b')]
    repo = init_repo(tmp_path / 'repo')
    commit_page(repo, old)
    before = (repo / 'index.html').read_text(encoding='utf-8')
    new = [item('a')]
    assert build_hub.apply(repo, build_hub.render(new, DAY), new) == 1
    assert (repo / 'index.html').read_text(encoding='utf-8') == before


def test_apply_allows_decrease_with_flag(tmp_path):
    old = [item('a'), item('b')]
    repo = init_repo(tmp_path / 'repo')
    commit_page(repo, old)
    new = [item('a')]
    assert build_hub.apply(repo, build_hub.render(new, DAY), new, allow_remove=True) == 0
    assert build_hub.slugs_in((repo / 'index.html').read_text(encoding='utf-8')) == {'a'}


def test_apply_blocks_dirty_clone(tmp_path):
    items = [item('a')]
    repo = init_repo(tmp_path / 'repo')
    commit_page(repo, items)
    (repo / 'stray.txt').write_text('x', encoding='utf-8')
    new = [item('a'), item('b')]
    assert build_hub.apply(repo, build_hub.render(new, DAY), new, deploy=True) == 1
    assert git('log', '-1', '--pretty=%s', cwd=repo).strip() == 'initial'
    assert git('status', '--porcelain', cwd=repo).strip().startswith('?? stray.txt')


def test_apply_blocks_diverged_remote(tmp_path):
    bare = tmp_path / 'origin.git'
    subprocess.run(['git', 'init', '--bare', '-b', 'main', str(bare)], check=True,
                   capture_output=True, text=True)
    git('clone', str(bare), 'repo', cwd=tmp_path)
    repo = tmp_path / 'repo'
    git('config', 'user.name', 'test', cwd=repo)
    git('config', 'user.email', 'test@example.com', cwd=repo)
    items = [item('a')]
    commit_page(repo, items)
    git('push', '-u', 'origin', 'main', cwd=repo)

    # 別 clone から origin を進める
    other = tmp_path / 'other'
    git('clone', str(bare), 'other', cwd=tmp_path)
    git('config', 'user.name', 'test', cwd=other)
    git('config', 'user.email', 'test@example.com', cwd=other)
    (other / 'README').write_text('x', encoding='utf-8')
    git('add', 'README', cwd=other)
    git('commit', '-m', 'remote change', cwd=other)
    git('push', cwd=other)

    new = [item('a'), item('b')]
    assert build_hub.apply(repo, build_hub.render(new, DAY), new, deploy=True) == 1
    assert git('log', '-1', '--pretty=%s', cwd=repo).strip() == 'initial'


def test_apply_deploys_and_pushes(tmp_path):
    bare = tmp_path / 'origin.git'
    subprocess.run(['git', 'init', '--bare', '-b', 'main', str(bare)], check=True,
                   capture_output=True, text=True)
    git('clone', str(bare), 'repo', cwd=tmp_path)
    repo = tmp_path / 'repo'
    git('config', 'user.name', 'test', cwd=repo)
    git('config', 'user.email', 'test@example.com', cwd=repo)
    commit_page(repo, [item('a')])
    git('push', '-u', 'origin', 'main', cwd=repo)

    new = [item('a'), item('b')]
    assert build_hub.apply(repo, build_hub.render(new, DAY), new, deploy=True) == 0

    subject = git('log', '-1', '--pretty=%s', cwd=repo).strip()
    assert subject.startswith('hub: 公開2件を反映（')
    assert git('log', '-1', '--pretty=%an', cwd=repo).strip() == build_hub.COMMIT_NAME
    assert git('rev-parse', 'HEAD', cwd=bare).strip() == git('rev-parse', 'HEAD', cwd=repo).strip()
    assert build_hub.slugs_in((repo / 'index.html').read_text(encoding='utf-8')) == {'a', 'b'}


# --- verify ---

class FakeResponse:
    def __init__(self, url):
        self.url = url


def test_verify_links_flags_bad_landing():
    items = [item('good', aff=AFF + '?n=1'), item('bad', aff=AFF + '?n=2'), item('boom', aff=AFF + '?n=3')]

    def get(url):
        if url == items[0]['affiliate']:
            return FakeResponse('https://item.rakuten.co.jp/shop/item/?scid=af_pc_etc')
        if url == items[1]['affiliate']:
            return FakeResponse('https://item.rakuten.co.jp/shop/item/')
        raise OSError('timeout')

    result = dict(build_hub.verify_links(items, get=get))
    assert result['good'] is None
    assert '着地が不正' in result['bad']
    assert '取得失敗' in result['boom']


def test_apply_deploy_commits_dry_run_artifact(tmp_path):
    """dry run が書いた index.html を --deploy が取りこぼさない。"""
    bare = tmp_path / 'origin.git'
    subprocess.run(['git', 'init', '--bare', '-b', 'main', str(bare)], check=True,
                   capture_output=True, text=True)
    git('clone', str(bare), 'repo', cwd=tmp_path)
    repo = tmp_path / 'repo'
    git('config', 'user.name', 'test', cwd=repo)
    git('config', 'user.email', 'test@example.com', cwd=repo)
    commit_page(repo, [item('a')])
    git('push', '-u', 'origin', 'main', cwd=repo)

    new = [item('a'), item('b')]
    text = build_hub.render(new, DAY)
    assert build_hub.apply(repo, text, new) == 0          # dry run が書き込む
    assert git('status', '--porcelain', cwd=repo).strip() == 'M index.html'

    assert build_hub.apply(repo, text, new, deploy=True) == 0
    assert git('log', '-1', '--pretty=%s', cwd=repo).strip().startswith('hub: 公開2件を反映（')
    assert git('status', '--porcelain', cwd=repo).strip() == ''
