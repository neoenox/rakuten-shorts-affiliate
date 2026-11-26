"""台本を ChatGPT / Google AI にレビューさせる（共通部品 ytkit.review の入口）。

既存の script_review.py（Gemini 用）は残す。こちらは共通部品を使う新しい入口。

usage:
  python scripts/script_review_common.py <slug>
  python scripts/script_review_common.py <slug> --target chatgpt
  python scripts/script_review_common.py <slug> --dry-run
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault('YT_PROJECT_ROOT', str(ROOT))

from ytkit.review.__main__ import main

if __name__ == '__main__':
    argv = sys.argv[1:]
    if argv and not argv[0].startswith('-'):
        slug = argv[0]
        path = ROOT / 'shorts' / slug / 'result.json'
        argv = ['run', str(path), '--adapter', 'rakuten_result',
                '--project', 'rakuten-shorts-affiliate', '--slug', slug] + argv[1:]
        argv += ['--out-dir', str(ROOT / 'shorts' / slug)]
    raise SystemExit(main(argv))
