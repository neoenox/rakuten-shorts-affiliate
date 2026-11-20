"""動画を描画せずに、説明欄・固定コメントだけを書き直す。

usage: python scripts/regen_text.py <slug>
描画済みの MP4 と SRT はそのまま。説明欄にリンクを足したいときなどに使う。
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import render_short as R  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description='説明欄と固定コメントのみを再生成する')
    ap.add_argument('slug')
    a = ap.parse_args()
    slug = a.slug
    slug_dir = ROOT / 'shorts' / slug
    data = R.load_json(slug_dir / 'result.json')
    conf = R.load_render_conf(slug_dir)
    draft = data.get('status') != 'ready'
    out_dir = ROOT / 'out' / ('draft' if draft else '')
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = slug + ('_DRAFT' if draft else '')

    (out_dir / (stem + '_description.md')).write_text(R.description(data, conf), encoding='utf-8')
    (out_dir / (stem + '_fixed_comment.md')).write_text(R.fixed_comment(data, conf), encoding='utf-8')
    print('updated:', out_dir / (stem + '_description.md'))
    print('--- head ---')
    print('\n'.join(R.description(data, conf).splitlines()[:8]))


if __name__ == '__main__':
    main()
