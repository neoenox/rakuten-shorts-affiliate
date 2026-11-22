"""FreeVideo（ローカル ComfyUI / MiniMax H3）で、Shorts 用の背景クリップを作る。

画面操作はしない。ComfyUI の HTTP API にグラフを投げ、/history をポーリングして mp4 を回収する。
グラフは FreeVideo アプリ自身が実行したもの（/history の prompt）と同じ形にそろえている。

前提:
  ・FreeVideo のランチャーで「Launch FreeVideo」を押し、http://127.0.0.1:8188 が応答すること
  ・出力は E:/FreeVideo/runtime/ComfyUI/output 配下（--output-root で変更可）

usage:
  python scripts/gen_freevideo.py shorts/kaito_plate/clips.json --slug kaito_plate
  python scripts/gen_freevideo.py shorts/kaito_plate/clips.json --slug kaito_plate --only clip1 --width 544 --height 960

clips.json:
  {"clips": [{"name": "clip1", "seconds": 7.0, "prompt": "..."}]}

出力: shorts/<slug>/art/clip_<name>.mp4（既にあるものは作らない。--force で上書き）
"""
import argparse
import json
import random
import shutil
import sys
import uuid
from pathlib import Path

from ytkit import freevideo as _fv   # 共通部品（E:\yt-shorts-kit）

BASE = _fv.DEFAULT_BASE
DEFAULT_OUTPUT_ROOT = _fv.DEFAULT_OUTPUT_ROOT
ROOT = Path(__file__).resolve().parents[1]


def post(path, body):
    return _fv.post(path, body, BASE)


def get(path):
    return _fv.get(path, BASE)


def graph(text, w, h, seconds, seed):
    """FreeVideo アプリが実行したのと同じ2ノード構成（実装は ytkit.freevideo）。"""
    return _fv.graph(text, w, h, seconds, seed)


def queue_state():
    return _fv.queue_state(BASE)


def wait(pid, limit=3600, poll=15):
    return _fv.wait(pid, BASE, limit, poll)


def video_of(entry, output_root):
    return _fv.video_of(entry, output_root)


def resolve_seed(clip):
    """spec に seed が無ければ生成して返す（後で spec に保存する）。"""
    return clip.get('seed') or random.randint(1, 2 ** 48)


def save_spec(path, spec):
    """自動生成した seed を失わないよう clips.json へ書き戻す。"""
    Path(path).write_text(json.dumps(spec, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    ap = argparse.ArgumentParser(description='FreeVideo で背景クリップを作る')
    ap.add_argument('spec')
    ap.add_argument('--slug', required=True)
    ap.add_argument('--width', type=int, default=544)
    ap.add_argument('--height', type=int, default=960)
    ap.add_argument('--only', nargs='*')
    ap.add_argument('--force', action='store_true')
    ap.add_argument('--output-root', default=str(DEFAULT_OUTPUT_ROOT))
    ap.add_argument('--timeout', type=int, default=3600)
    args = ap.parse_args()

    spec = json.loads(Path(args.spec).read_text(encoding='utf-8'))
    art = ROOT / 'shorts' / args.slug / 'art'
    art.mkdir(parents=True, exist_ok=True)
    out_root = Path(args.output_root)
    only = set(args.only or [])

    for clip in spec['clips']:
        name = clip['name']
        if only and name not in only:
            continue
        dest = art / ('clip_%s.mp4' % name)
        if dest.exists() and not args.force:
            print('[skip] %s は既にある' % dest.name)
            continue
        seed = resolve_seed(clip)
        body = {'prompt': graph(clip['prompt'], args.width, args.height,
                                clip.get('seconds', 7.0), seed),
                'client_id': str(uuid.uuid4())}
        pid = post('/prompt', body)['prompt_id']
        print('[queued] %s -> %s (seed=%d)' % (name, pid, seed), flush=True)
        entry, st = wait(pid, args.timeout)
        if st != 'success':
            print('[failed] %s: %s' % (name, st), flush=True)
            if entry:
                print(json.dumps(entry.get('status', {}), ensure_ascii=False)[:800])
            continue
        src = video_of(entry, out_root)
        if not src or not src.exists():
            print('[failed] %s: 出力mp4が見つからない (%s)' % (name, src))
            continue
        shutil.copy2(src, dest)
        clip['seed'] = seed
        save_spec(args.spec, spec)
        outputs = (entry or {}).get('outputs') or {}
        node = outputs.get('1') or {}
        summaries = node.get('freevideo_summary') or [{}]
        summary = summaries[0]
        geo = summary.get('geometry', {})
        print('[done] %s  %.2fs / %sx%s / %.0fs で生成 -> %s'
              % (name, geo.get('seconds', 0), geo.get('width'), geo.get('height'),
                 summary.get('sample_seconds', 0), dest.relative_to(ROOT)), flush=True)

    print('\n次の手順: shorts/<slug>/render.json の "clips" に使うシーンを書き、'
          'python scripts/render_short.py <slug> で描画する')


if __name__ == '__main__':
    sys.exit(main())
