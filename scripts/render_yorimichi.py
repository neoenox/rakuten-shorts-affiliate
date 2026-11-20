"""寄り道ラボ方式（make_short2.py の想法）で Shorts を描画する。

入力は `shorts_standard.py to-spec` が作る `shorts/<slug>/short_spec.json`。
台本の正は `shorts/<slug>/result.json` で、claim_ids や visual はここから補う。
PR・種別ラベル・出典・アフィリエイト説明欄はこのリポジトリの規約を満たす。

usage:
  python scripts/render_yorimichi.py <slug> --plan
  python scripts/render_yorimichi.py <slug> [--out-dir out]
"""
import argparse
import sys
from pathlib import Path

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


def description(data, conf):
    """既存の説明欄ジェネレータを再利用し、規約表記を維持する。"""
    return R.description(data, conf)


def fixed_comment(data, conf):
    return R.fixed_comment(data, conf)


def main():
    ap = argparse.ArgumentParser(description='寄り道ラボ方式で Shorts を描画する')
    ap.add_argument('slug')
    ap.add_argument('--plan', action='store_true')
    ap.add_argument('--out-dir', default='out')
    ap.add_argument('--thumb-at', type=float, default=1.2)
    ap.parse_args()
    raise SystemExit('未実装: --plan / 描画は次のステップで追加します')


if __name__ == '__main__':
    sys.exit(main())
