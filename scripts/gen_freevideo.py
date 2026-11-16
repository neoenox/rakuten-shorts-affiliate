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
import time
import urllib.request
import uuid
from pathlib import Path

BASE = 'http://127.0.0.1:8188'
DEFAULT_OUTPUT_ROOT = Path('E:/FreeVideo/runtime/ComfyUI/output')
ROOT = Path(__file__).resolve().parents[1]


def post(path, body):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode(),
                                 headers={'Content-Type': 'application/json'})
    raw = urllib.request.urlopen(req, timeout=60).read()
    return json.loads(raw) if raw.strip() else {}


def get(path):
    return json.loads(urllib.request.urlopen(BASE + path, timeout=30).read())


def graph(text, w, h, seconds, seed):
    """FreeVideo アプリが実行したのと同じ2ノード構成（/history の prompt で確認）。"""
    return {
        '1': {'class_type': 'FreeVideoGenerate', 'inputs': dict(
            text=text, width=w, height=h, seconds=float(seconds), seed=seed,
            two_pass=True, base_steps=8, refine_steps=3,
            force_regenerate=False, preview=False,
            refine_from='', continue_from='', frames=0,
            first_frame_reference=False, voice_reference=False, hide_tail=False,
            step_cache='none', upscale_factor='2', allow_empty_prompt=False,
            media=['2', 0])},
        '2': {'class_type': 'FreeVideoMedia', 'inputs': {'assets': '[]', 'audio_use': 'reference'}},
    }


def queue_state():
    q = get('/queue')
    return len(q['queue_running']), len(q['queue_pending'])


def wait(pid, limit=3600, poll=15):
    t0 = time.time()
    while time.time() - t0 < limit:
        try:
            h = get('/history/' + pid)
        except Exception:
            h = {}
        if pid in h:
            st = h[pid].get('status', {}).get('status_str')
            return h[pid], st
        try:
            get('/queue')
        except Exception:
            return None, 'server_down'
        time.sleep(poll)
    return None, 'timeout'


def video_of(entry, output_root):
    for node in entry.get('outputs', {}).values():
        for item in node.get('images', []):
            if str(item.get('filename', '')).endswith('.mp4'):
                return output_root / item.get('subfolder', '') / item['filename']
    return None


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
        seed = clip.get('seed') or random.randint(1, 2 ** 48)
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
        summary = (entry['outputs'].get('1', {}).get('freevideo_summary') or [{}])[0]
        geo = summary.get('geometry', {})
        print('[done] %s  %.2fs / %sx%s / %.0fs で生成 -> %s'
              % (name, geo.get('seconds', 0), geo.get('width'), geo.get('height'),
                 summary.get('sample_seconds', 0), dest.relative_to(ROOT)), flush=True)

    print('\n次の手順: shorts/<slug>/render.json の "clips" に使うシーンを書き、'
          'python scripts/render_short.py <slug> で描画する')


if __name__ == '__main__':
    sys.exit(main())
