"""寄り道ラボ方式（make_short2.py の想法）で Shorts を描画する。

入力は `shorts_standard.py to-spec` が作る `shorts/<slug>/short_spec.json`。
台本の正は `shorts/<slug>/result.json` で、claim_ids や visual はここから補う。
PR・種別ラベル・出典・アフィリエイト説明欄はこのリポジトリの規約を満たす。

usage:
  python scripts/render_yorimichi.py <slug> --plan
  python scripts/render_yorimichi.py <slug> [--out-dir out]
"""
import argparse
import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import render_short as R  # noqa: E402


def load_json(path):
    return R.load_json(path)


def load_render_conf(slug_dir):
    return R.load_render_conf(slug_dir)


def load_spec(slug_dir):
    return load_json(slug_dir / 'short_spec.json')


def spec_to_data(spec):
    """to-spec 形式を render_short 共通ヘルパが読む形へ変換する。"""
    scenes = []
    for s in spec.get('scenes') or []:
        captions = [x for x in (s.get('big'), s.get('sub')) if x]
        scenes.append({
            'narration': s.get('text') or '',
            'caption': captions,
            'claim_ids': [],
            'visual': '',
        })
    return {
        'title': spec.get('title') or '',
        'hook': spec.get('hook') or '',
        'duration_sec': spec.get('sec') or spec.get('duration_sec') or 0,
        'status': spec.get('status') or 'needs_review',
        'scenes': scenes,
        'claims': spec.get('claims') or [],
        'needs_research': spec.get('needs_research') or [],
    }


def merge_evidence(data, result):
    """result.json から claim_ids / visual / status を描画データへ戻す。"""
    result_scenes = result.get('scenes') or []
    for i, sc in enumerate(data['scenes']):
        src = result_scenes[i] if i < len(result_scenes) else {}
        sc['claim_ids'] = src.get('claim_ids') or []
        sc['visual'] = src.get('visual') or ''
    if result.get('status'):
        data['status'] = result['status']
    if result.get('duration_sec'):
        data['duration_sec'] = result['duration_sec']


def source_label(sc, conf):
    labels = conf.get('source_labels') or {}
    for cid in sc.get('claim_ids') or []:
        if cid in labels:
            return '出典: ' + labels[cid]
    return conf.get('source_fallback', '') if sc.get('claim_ids') else ''


def current_caption(text, t, start, dur):
    """ナレーションを時間割り振りした字幕の現在行を返す。"""
    chunks = R.subtitle_chunks(text)
    if not chunks:
        return ''
    weights = [len(c) for c in chunks]
    total = sum(weights) or 1
    elapsed = max(0.0, min(dur, t - start))
    acc = 0
    for chunk, weight in zip(chunks, weights, strict=True):
        acc += dur * weight / total
        if elapsed < acc:
            return chunk
    return chunks[-1]


def draw_frame(im, sc, data, conf, scene_i, t, start, dur, kind, caption_alpha=1.0):
    """寄り道ラボ風の画面に、このプロジェクトの必須表記を重ねる。"""
    d = R.ImageDraw.Draw(im, 'RGBA')

    def solid(c, al=255):
        return c + (al,)

    def faded(c, al=255):
        return c + (int(al * caption_alpha),)

    # 見出し（寄り道ラボは1行58px。ここでは折り返しを許容する）
    lines = R.wrap(d, data['title'], R.font(52, 700), 900)[:2]
    y = 196
    for line in lines:
        d.text((540, y), line, font=R.font(52, 700), fill=solid(R.WHITE, 240), anchor='mm',
               stroke_width=4, stroke_fill=solid((0, 0, 0), 140))
        y += 62
    d.line([(120, y + 12), (960, y + 12)], fill=solid(R.GOLD, 220), width=4)

    # PR（全編。フェードしない）
    d.rounded_rectangle((40, 96, 158, 168), 14, fill=solid((0, 0, 0), 150),
                        outline=solid(R.GOLD, 235), width=3)
    d.text((99, 132), 'PR', font=R.font(42, 700), fill=solid(R.GOLD), anchor='mm')

    # 種別ラベル（実写と混同させない。こちらもフェードしない）
    lab = R.type_label(kind)
    f = R.font(30, 600)
    tw = d.textlength(lab, font=f)
    d.rounded_rectangle((R.W - 44 - tw - 40, 108, R.W - 44, 160), 12,
                        fill=solid((0, 0, 0), 140))
    d.text((R.W - 64, 134), lab, font=f, fill=solid((232, 232, 226), 235), anchor='rm')

    caps = [c for c in (sc.get('caption') or []) if c]
    if caps:
        big = caps[0]
        fbig = R.font(88, 700)
        for line in R.wrap(d, big, fbig, 880)[:2]:
            d.text((540, 520), line, font=fbig, fill=faded(R.GOLD), anchor='mm',
                   stroke_width=5, stroke_fill=faded((0, 0, 0), 150))
        if len(caps) > 1:
            d.rounded_rectangle((60, 800, 960, 960), 18, fill=faded((7, 24, 36), 215))
            d.text((540, 880), caps[1], font=R.font(44, 700), fill=faded(R.WHITE), anchor='mm')

    src = source_label(sc, conf)
    if src:
        fsrc = R.font(28, 500)
        while fsrc.size > 22 and d.textlength(src, font=fsrc) > 900:
            fsrc = R.font(fsrc.size - 2, 500)
        d.rounded_rectangle((60, 1170, 1020, 1230), 10, fill=faded((5, 14, 24), 180))
        d.text((540, 1200), src, font=fsrc, fill=faded((235, 238, 242), 235), anchor='mm')

    cap = current_caption(sc.get('narration') or '', t, start, dur)
    if cap:
        fcap = R.font(56, 600)
        lines = R.wrap(d, cap, fcap, 880)
        while len(lines) * int(fcap.size * 1.35) > 260 and fcap.size > 40:
            fcap = R.font(fcap.size - 4, 600)
            lines = R.wrap(d, cap, fcap, 880)
        lh = int(fcap.size * 1.35)
        h = len(lines) * lh + 42
        y0 = 1540 - h
        d.rounded_rectangle((50, y0, 960, 1540), 16, fill=faded((7, 24, 36), 225))
        y = y0 + 21 + lh // 2
        for line in lines:
            d.text((505, y), line, font=fcap, fill=faded((255, 252, 239), 255), anchor='mm')
            y += lh
    return im


def plan(slug, speaker=None, speed=None):
    """VOICEVOX の実測尺で result.json の start/end/duration を更新する。"""
    sd = ROOT / 'shorts' / slug
    result_path = sd / 'result.json'
    data = load_json(result_path)
    conf = load_render_conf(sd)
    sp = speaker or conf.get('speaker', '青山龍星')
    spd = speed if speed is not None else float(conf.get('speed', 0.95))
    segs = R.synthesize(sd, data, conf, sp, spd)
    starts, spans, total = R.plan_timing([s['dur'] for s in segs])
    R.write_timing(result_path, data, starts, spans, total)
    print(f'実測 {total:.2f} 秒 / {len(spans)} シーン。次に shorts_standard.py check を実行する')
    return total


def output_paths(slug, status, out_dir='out'):
    draft = status != 'ready'
    directory = ROOT / out_dir / ('draft' if draft else '')
    stem = slug + ('_DRAFT' if draft else '')
    return (
        directory, stem,
        directory / (stem + '.mp4'),
        directory / (stem + '_thumb.jpg'),
        directory / (stem + '_description.md'),
        directory / (stem + '_fixed_comment.md'),
    )


def load_bases(sd, spec):
    bases = []
    for s in spec.get('scenes') or []:
        raw = Path(s.get('art') or spec.get('art') or '')
        path = raw if raw.is_absolute() else ROOT / raw
        bases.append(R.cover(Image.open(path).convert('RGB'), R.W, R.H))
    return bases


def apply_timing(data, starts, total):
    for i, sc in enumerate(data['scenes']):
        sc['start'] = starts[i]
        sc['end'] = starts[i + 1] if i + 1 < len(starts) else total
    data['duration_sec'] = total


def scene_at(data, t):
    for i, sc in enumerate(data['scenes']):
        if sc['start'] <= t < sc['end']:
            return i
    return max(0, len(data['scenes']) - 1)


def frame_image(data, bases, clipf, si, t):
    sc = data['scenes'][si]
    dur = max(0.01, sc['end'] - sc['start'])
    k = max(0.0, min(1.0, (t - sc['start']) / dur))
    if si in clipf:
        d, n = clipf[si]
        idx = min(n, max(1, int((t - sc['start']) * R.FPS) + 1))
        im = Image.open(d / f'f_{idx:05d}.jpg').convert('RGB')
    else:
        im = R.kenburns(bases[si], k)
    im = R.bottom_shade(im)
    kind = (data.get('_kinds') or ['ai'] * len(data['scenes']))[si]
    return draw_frame(im, sc, data, data.get('_conf') or {}, si, t, sc['start'], dur,
                      kind, caption_alpha=R.caption_alpha(t, sc['start']))


def render_frames(data, bases, kinds, conf, total, work, out_mp4, ff, clipf):
    data['_kinds'] = kinds
    data['_conf'] = conf
    proc = subprocess.Popen([ff, '-y', '-v', 'warning', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                             '-s', f'{R.W}x{R.H}', '-r', str(R.FPS), '-i', 'pipe:0',
                             '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
                             '-pix_fmt', 'yuv420p', str(out_mp4)], stdin=subprocess.PIPE)
    assert proc.stdin is not None
    for fi in range(round(total * R.FPS)):
        t = fi / R.FPS
        si = scene_at(data, t)
        proc.stdin.write(frame_image(data, bases, clipf, si, t).tobytes())
    proc.stdin.close()
    proc.wait()
    if proc.returncode:
        raise SystemExit('ffmpeg の映像エンコードに失敗')


def render(slug, out_dir='out', thumb_at=1.2, speaker=None, speed=None):
    sd = ROOT / 'shorts' / slug
    spec_path = sd / 'short_spec.json'
    if not spec_path.is_file():
        raise SystemExit(f'spec が無い: {spec_path}（先に shorts_standard.py to-spec を実行）')
    spec = load_spec(sd)
    result = load_json(sd / 'result.json')
    conf = load_render_conf(sd)
    data = spec_to_data(spec)
    merge_evidence(data, result)

    sp = speaker or conf.get('speaker', '青山龍星')
    spd = speed if speed is not None else float(conf.get('speed', 0.95))
    segs = R.synthesize(sd, data, conf, sp, spd)
    starts, spans, total = R.plan_timing([s['dur'] for s in segs])
    if abs((result.get('duration_sec') or 0) - total) > 0.2:
        raise SystemExit('result.json の尺が実測と違う。先に --plan と check を実行する')
    apply_timing(data, starts, total)

    directory, stem, mp4, thumb, desc_path, comment_path = output_paths(slug, data['status'], out_dir)
    directory.mkdir(parents=True, exist_ok=True)
    work = ROOT / 'cache' / ('yorimichi_' + slug)
    work.mkdir(parents=True, exist_ok=True)
    ff = R.ffmpeg_bin()
    clipf = R.prepare_clip_frames(sd, conf, data, work, ff)
    narration = R.build_audio(segs, starts, total, work)
    bases = load_bases(sd, spec)
    kinds = [(conf.get('art_types') or {}).get(str(i), 'ai') for i in range(1, len(data['scenes']) + 1)]

    raw = work / 'raw.mp4'
    render_frames(data, bases, kinds, conf, total, work, raw, ff, clipf)
    R.mux(ff, raw, narration, total, mp4, bgm=conf.get('bgm'))
    R.write_srt(directory / (stem + '_subtitles.srt'), data)
    desc_path.write_text(description(data, conf), encoding='utf-8')
    comment_path.write_text(fixed_comment(data, conf), encoding='utf-8')

    thumb_t = min(max(0.0, thumb_at), total - 0.1)
    data['_kinds'] = kinds
    data['_conf'] = conf
    image = frame_image(data, bases, clipf, scene_at(data, thumb_t), thumb_t)
    image.save(thumb, quality=92)
    print(f'完成: {mp4}')
    if data['status'] != 'ready':
        print(f'【下書き】status={data["status"]}。公開しないこと。')
    return mp4


def description(data, conf):
    """既存の説明欄ジェネレータを再利用し、規約表記を維持する。"""
    return R.description(data, conf)


def fixed_comment(data, conf):
    return R.fixed_comment(data, conf)


def main():
    ap = argparse.ArgumentParser(description='寄り道ラボ方式で Shorts を描画する')
    ap.add_argument('slug')
    ap.add_argument('--plan', action='store_true', help='実測尺で result.json を更新する')
    ap.add_argument('--out-dir', default='out')
    ap.add_argument('--thumb-at', type=float, default=1.2)
    ap.add_argument('--speaker')
    ap.add_argument('--speed', type=float)
    args = ap.parse_args()

    if args.plan:
        plan(args.slug, args.speaker, args.speed)
        return 0
    render(args.slug, args.out_dir, args.thumb_at, args.speaker, args.speed)
    return 0


if __name__ == '__main__':
    sys.exit(main())
