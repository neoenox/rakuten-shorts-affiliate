"""商品一覧ページ（hub）の HTML を生成し、公開リポジトリへ反映する。

`shorts/<slug>/publish.json`（公開の事実）と `render.json`（商品・リンク）から作り、
clone 済みの公開リポジトリ（既定 `../kurashi-hantei`）の `index.html` に書く。手で HTML を書かない。

使い方:
  python scripts/build_hub.py                  # 生成・検査・差分表示まで（commit しない）
  python scripts/build_hub.py --deploy         # 検査を通ったときだけ commit して push
  python scripts/build_hub.py --verify         # リンクが生きているかを確認（書き込みなし）
  python scripts/build_hub.py --allow-remove --deploy   # カードが減る変更を明示的に許可

方針（docs/superpowers/specs/2026-11-19-revenue-path-design.md）:
  - 価格は載せない（変動する）
  - 商品画像は使わない（楽天の画像は複製・改変が禁止）
  - レビュー本文は載せない
  - ページ上部にアフィリエイト広告の明示
  - 正は公開リポジトリの index.html 1つ。このリポジトリに写しは置かない

deploy の停止条件（fail-closed）:
  1. 検査 FAIL        2. clone が無い／git 管理外
  3. clone が dirty    4. origin/main と HEAD がずれている
  5. カードが減る（--allow-remove が無いとき）
  6. 差分ゼロ → 何もせず成功
"""
import argparse
import html
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPO = ROOT.parent / 'kurashi-hantei'
CHANNEL_URL = 'https://www.youtube.com/@kurashi_hantei'
CHANNEL_NAME = '暮らしの判断メモ'
BRANCH = 'main'
COMMIT_NAME = 'neoenox'
COMMIT_EMAIL = 'neoenox@users.noreply.github.com'


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def collect(root=None):
    """公開済みの動画から、商品カードの材料を集める。"""
    root = Path(root or (ROOT / 'shorts'))
    items = []
    for pub_path in sorted(root.glob('*/publish.json')):
        slug = pub_path.parent.name
        pub = load(pub_path)
        if pub.get('visibility') != 'public':
            continue
        render_path = pub_path.parent / 'render.json'
        conf = load(render_path) if render_path.exists() else {}
        aff = (conf.get('affiliate') or {}).get('url') or ''
        product = (pub.get('product') or {}).get('name') or conf.get('product_name') or ''
        if not aff or not product:
            print(f'  skip {slug}: 商品名かリンクが無い', file=sys.stderr)
            continue
        items.append({
            'slug': slug,
            'title': pub.get('title') or conf.get('product_name') or slug,
            'product': product,
            'affiliate': aff,
            'video_id': pub.get('video_id'),
            'published_at': pub.get('published_at') or '',
        })
    # 新しい順（日付が同じなら slug で安定化）
    items.sort(key=lambda x: (x['published_at'], x['slug']), reverse=True)
    return items


CARD = """
    <li class="card" data-slug="{slug}">
      <p class="product">{product}</p>
      <p class="video">紹介した動画: <a href="https://www.youtube.com/shorts/{video_id}">{title}</a></p>
      <a class="cta" href="{affiliate}" rel="nofollow sponsored noopener" target="_blank">楽天で見る</a>
    </li>"""

PAGE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{channel}｜紹介した商品の一覧</title>
<meta name="description" content="{channel}の動画で紹介した商品の一覧です。">
<style>
  :root {{ color-scheme: dark; }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 28px 18px 56px; background: #12161d; color: #f2efe6;
    font-family: system-ui, -apple-system, "Hiragino Sans", "Noto Sans JP", sans-serif;
    line-height: 1.7; -webkit-text-size-adjust: 100%;
  }}
  main {{ max-width: 720px; margin: 0 auto; }}
  h1 {{ font-size: 22px; margin: 0 0 6px; letter-spacing: .02em; }}
  .lead {{ color: #a8b2be; font-size: 14px; margin: 0 0 18px; }}
  .pr {{
    border: 1px solid #6b5a2e; background: #241f14; color: #e8cf92;
    font-size: 13px; padding: 10px 12px; border-radius: 10px; margin: 0 0 22px;
  }}
  ul {{ list-style: none; margin: 0; padding: 0; display: grid; gap: 14px; }}
  .card {{ border: 1px solid #2c3642; background: #171d26; border-radius: 14px; padding: 16px; }}
  .product {{ margin: 0 0 6px; font-weight: 700; font-size: 16px; }}
  .video {{ margin: 0 0 12px; font-size: 13px; color: #9aa6b4; }}
  .video a {{ color: #9ec3ea; text-decoration: none; }}
  .cta {{
    display: inline-block; padding: 10px 18px; border-radius: 999px;
    background: #bf0000; color: #fff; text-decoration: none; font-weight: 700; font-size: 14px;
  }}
  footer {{ margin-top: 28px; font-size: 13px; color: #8b96a4; }}
  footer a {{ color: #9ec3ea; }}
</style>
</head>
<body>
<main>
  <h1>{channel}</h1>
  <p class="lead">動画で紹介した商品の一覧です。動画は30〜45秒で、数字は公的資料にもとづいています。</p>
  <p class="pr">このページはアフィリエイト広告を含みます。商品リンクから購入すると、当チャンネルに報酬が発生することがあります。価格・在庫・仕様は必ず販売元のページでご確認ください。</p>
  <ul>{cards}
  </ul>
  <footer>
    <p><a href="{channel_url}">チャンネルを見る（{channel}）</a></p>
    <p>更新: {updated} ／ 掲載 {count} 件</p>
  </footer>
</main>
</body>
</html>
"""


def render(items, today=None):
    cards = ''.join(
        CARD.format(
            slug=html.escape(i['slug']),
            product=html.escape(i['product']),
            title=html.escape(i['title']),
            video_id=html.escape(i['video_id'] or ''),
            affiliate=html.escape(i['affiliate']),
        )
        for i in items
    )
    return PAGE.format(
        channel=CHANNEL_NAME,
        channel_url=CHANNEL_URL,
        cards=cards,
        updated=(today or date.today()).isoformat(),
        count=len(items),
    )


def check(text, items):
    problems = []
    if 'アフィリエイト広告を含みます' not in text:
        problems.append('PR表記が無い')
    if '<img' in text:
        problems.append('画像が入っている（商品画像は使わない）')
    # 価格は載せない。動画タイトルには金額（出典のある主張）が入るので、商品名だけを見る。
    for i in items:
        if '円' in i['product']:
            problems.append(f"商品名に価格らしき文字: {i['slug']}")
    for i in items:
        if i['affiliate'] not in text:
            problems.append(f"リンクが無い: {i['slug']}")
    if items and 'rel="nofollow sponsored' not in text:
        problems.append('rel="nofollow sponsored" が無い')
    return problems


def slugs_in(text):
    return set(re.findall(r'data-slug="([^"]+)"', text or ''))


def verify_links(items, get=None):
    """各アフィリエイトリンクが商品ページに着地するかを見る（警告のみ・課金なし）。"""
    if get is None:
        import requests

        def _get(url):
            return requests.get(url, timeout=20, allow_redirects=True,
                                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})

        get = _get
    results = []
    for i in items:
        try:
            r = get(i['affiliate'])
            final = getattr(r, 'url', '')
            ok = final.startswith('https://item.rakuten.co.jp/') and 'scid=' in final
            results.append((i['slug'], None if ok else f'着地が不正: {final[:90]}'))
        except Exception as e:  # ネットワーク失敗は警告に留める
            results.append((i['slug'], f'取得失敗: {e}'))
    return results


def git(repo, *args, check_=True):
    cp = subprocess.run(['git', '-C', str(repo), *args],
                        capture_output=True, text=True, encoding='utf-8')
    if check_ and cp.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} 失敗: {cp.stderr.strip() or cp.stdout.strip()}")
    return cp


def ensure_repo(repo):
    if not (repo / '.git').exists():
        raise RuntimeError(f'clone が無い: {repo}（gh repo clone neoenox/kurashi-hantei {repo}）')


def ensure_clean(repo):
    """index.html 以外に未 commit の変更が無いことを確かめる。

    index.html はこれから生成物で上書きするので、dry run の書き込みは許す。
    """
    out = [line for line in git(repo, 'status', '--porcelain').stdout.splitlines()
           if line.strip() and not line.strip().endswith(' index.html')]
    if out:
        raise RuntimeError('clone に未 commit の変更がある:\n' + '\n'.join(out))


def index_dirty(repo):
    return bool(git(repo, 'status', '--porcelain', '--', 'index.html').stdout.strip())


def ensure_synced(repo):
    git(repo, 'fetch', '--quiet', 'origin', BRANCH)
    head = git(repo, 'rev-parse', 'HEAD').stdout.strip()
    remote = git(repo, 'rev-parse', f'origin/{BRANCH}').stdout.strip()
    if head != remote:
        raise RuntimeError(f'origin/{BRANCH} と HEAD がずれている（HEAD {head[:8]} / origin {remote[:8]}）。手で揃えること')


def commit_and_push(repo, old_slugs, new_slugs, items):
    added = new_slugs - old_slugs
    removed = old_slugs - new_slugs
    names = {i['slug']: i['product'] for i in items}
    body = [f'+ {s} {names.get(s, "")}'.rstrip() for s in sorted(added)]
    body += [f'- {s}' for s in sorted(removed)]
    git(repo, 'add', 'index.html')
    subject = f'hub: 公開{len(items)}件を反映（{date.today().isoformat()}）'
    args = ['-c', f'user.name={COMMIT_NAME}', '-c', f'user.email={COMMIT_EMAIL}',
            'commit', '-m', subject]
    if body:
        args += ['-m', '\n'.join(body)]
    git(repo, *args)
    git(repo, 'push', 'origin', f'HEAD:{BRANCH}')
    return subject


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', default=str(DEFAULT_REPO))
    ap.add_argument('--deploy', action='store_true', help='commit して push する')
    ap.add_argument('--allow-remove', action='store_true', help='カードが減る変更を許可する')
    ap.add_argument('--verify', action='store_true', help='リンクの生存確認だけを行う')
    a = ap.parse_args()

    items = collect()
    text = render(items)
    problems = check(text, items)
    print(f'生成: {len(items)} 件')
    for i in items:
        print(f"  - {i['published_at']} {i['product'][:34]}")

    if problems:
        print('検査: FAIL')
        for p in problems:
            print('  -', p)
        return 1
    print('検査: PASS（PR表記・画像なし・価格なし・リンクとrel）')

    if a.verify:
        bad = 0
        for slug, err in verify_links(items):
            print(f'  {slug}: ' + (err or 'OK'))
            bad += 1 if err else 0
        print(f'リンク確認: {"FAIL" if bad else "PASS"}（{len(items)} 件）')
        return 1 if bad else 0

    return apply(Path(a.repo), text, items, a.allow_remove, a.deploy)


def apply(repo, text, items, allow_remove=False, deploy=False):
    """生成済み HTML を clone へ反映する。戻り値は exit code。"""
    try:
        ensure_repo(repo)
    except RuntimeError as e:
        print('中断:', e)
        return 1

    page = repo / 'index.html'
    old = page.read_text(encoding='utf-8') if page.exists() else ''
    old_slugs = slugs_in(old)
    new_slugs = {i['slug'] for i in items}
    removed = old_slugs - new_slugs
    if removed and not allow_remove:
        print('中断: カードが減る変更（--allow-remove で明示許可）:', ', '.join(sorted(removed)))
        return 1

    if deploy:
        try:
            ensure_clean(repo)
            ensure_synced(repo)
        except RuntimeError as e:
            print('中断:', e)
            return 1

    if text == old:
        # dry run の書き込みなどで作業ツリーだけが古い場合は、commit まで進める
        if deploy and index_dirty(repo):
            try:
                subject = commit_and_push(repo, old_slugs, new_slugs, items)
            except RuntimeError as e:
                print('中断（commit/push）:', e)
                return 1
            print(f'push 完了: {subject}')
            return 0
        print('反映: 変更なし（no-op）')
        return 0

    page.write_text(text, encoding='utf-8')
    print(f'反映: {page}')

    if not deploy:
        print(git(repo, 'diff', '--stat', '--', 'index.html', check_=False).stdout.strip())
        print('未 commit。--deploy で commit して push する。')
        return 0

    try:
        subject = commit_and_push(repo, old_slugs, new_slugs, items)
    except RuntimeError as e:
        print('中断（commit/push）:', e)
        return 1
    print(f'push 完了: {subject}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
