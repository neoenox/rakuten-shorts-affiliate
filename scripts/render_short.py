"""制作標準の台本（result.json）から、9:16 の Shorts 用 MP4 を作る。

方針:
  ・台本は shorts-standard が正。本スクリプトは形式検査をしない（shorts_standard.py check が担当）。
  ・「PR」を全編に焼き込む（ステマ告示。冒頭だけでは足りないとされる）。
  ・AI生成の情景には「イメージ（AI生成）」、図解には「模式図」を画面に出す（実写と混同させない）。
  ・ナレーションは VOICEVOX。実測した音声の尺を結果に反映してから描画する（--plan）。
    検査済みの result.json と描画がずれないよう、描画は result.json の start/end をそのまま使う。

usage:
  python scripts/render_short.py <slug> --plan
      音声を合成し、実測尺で result.json の start/end/duration_sec を更新する（描画しない）。
      更新したら python scripts/shorts_standard.py check をやり直すこと。

  python scripts/render_short.py <slug> [--out-dir out]
      MP4・SRT・説明欄・固定コメント・サムネを作る。
      status が ready 以外なら out/draft/ に「下書き」として書き、公開前の確認事項を表示する。

  python scripts/render_short.py <slug> --plan --speaker 青山龍星 --speed 0.95
      話者と話速の指定（render.json の設定より優先）。

必要なもの:
  ・VOICEVOX ENGINE（127.0.0.1:50021）。話者は /speakers から名前で引く。
  ・ffmpeg。PATH → 環境変数 FFMPEG → 旧プロジェクトの tools/ffmpeg の順で探す。
  ・shorts/<slug>/result.json、shorts/<slug>/art/scene_01.png …（シーン数ぶん）
  ・任意: shorts/<slug>/render.json（話者・話速・映像種別・出典ラベル）
"""
import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BASE = 'http://127.0.0.1:50021'
W, H, FPS = 1080, 1920, 30

# 色（既存の寄り道ラボと同じ調子）
INK = (12, 16, 22)
WHITE = (246, 244, 236)
DIM = (176, 186, 194)
GOLD = (239, 201, 118)

# 時間設計（制作標準: 1シーン3〜9秒、全体30〜45秒）
MIN_SCENE, MAX_SCENE = 3.0, 9.0
MIN_TOTAL, MAX_TOTAL = 30.0, 45.0
GAP = 0.35          # シーン間の無音
TAIL = 0.45         # 最後の余韻
LEAD = 0.10         # シーン頭から声が出るまで

FONT_PATH = Path('C:/Windows/Fonts/NotoSansJP-VF.ttf')
_fonts = {}


def font(size, weight=600):
    key = (size, weight)
    if key not in _fonts:
        f = ImageFont.truetype(str(FONT_PATH), size)
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass
        _fonts[key] = f
    return _fonts[key]


def ffprobe_bin(ff):
    if Path(ff).name.lower() == 'ffmpeg.exe':
        p = Path(ff).with_name('ffprobe.exe')
        if p.exists():
            return str(p)
    return shutil.which('ffprobe') or ff


def ffmpeg_bin():
    cands = [os.environ.get('FFMPEG'), shutil.which('ffmpeg'),
             r'E:\rekishikaisetu-honnoji\tools\ffmpeg\bin\ffmpeg.exe']
    for c in cands:
        if c and Path(c).exists():
            return str(c)
    raise SystemExit('ffmpeg が見つからない。PATH か環境変数 FFMPEG で指定する')


def wrap(draw, text, f, maxw):
    """幅 maxw で折り返す（日本語は単純な詰めで足りる。句読点の行頭禁則だけ避ける）。"""
    lines, cur = [], ''
    for ch in text:
        if draw.textlength(cur + ch, font=f) > maxw and cur:
            if ch in '、。，．！？!?）」』':
                cur += ch
                lines.append(cur)
                cur = ''
                continue
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def load_json(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def load_render_conf(slug_dir):
    p = slug_dir / 'render.json'
    return load_json(p) if p.exists() else {}


# ---------------------------------------------------------------- 音声

def speaker_id(name, style='ノーマル'):
    sp = requests.get(BASE + '/speakers', timeout=30).json()
    for s in sp:
        if s['name'] == name:
            for st in s['styles']:
                if st['name'] == style:
                    return st['id']
            return s['styles'][0]['id']
    raise SystemExit('VOICEVOX に話者が居ない: %s（--speaker で指定）' % name)


def synthesize(slug_dir, data, conf, speaker, speed):
    """シーンごとに wav を作り、実測尺と読みを返す。既存の wav は再利用しない（尺が変わるとズレるため）。"""
    work = ROOT / 'cache' / ('render_' + slug_dir.name)
    work.mkdir(parents=True, exist_ok=True)
    sid = speaker_id(speaker, conf.get('style', 'ノーマル'))
    pron = {}
    pp = slug_dir / 'pron.json'
    if pp.exists():
        pron = load_json(pp)
    out = []
    for i, sc in enumerate(data['scenes']):
        text = sc['narration']
        for k, v in sorted(pron.items(), key=lambda z: -len(z[0])):
            text = text.replace(k, v)
        q = requests.post(BASE + '/audio_query', params={'text': text, 'speaker': sid}, timeout=120).json()
        q.update(speedScale=speed, intonationScale=1.0, prePhonemeLength=0.1, postPhonemeLength=0.3,
                 outputSamplingRate=24000)
        r = requests.post(BASE + '/synthesis', params={'speaker': sid}, json=q, timeout=180)
        r.raise_for_status()
        p = work / ('n_%02d.wav' % (i + 1))
        p.write_bytes(r.content)
        with wave.open(str(p)) as w:
            dur = w.getnframes() / w.getframerate()
            rate = w.getframerate()
            pcm = np.frombuffer(w.readframes(w.getnframes()), np.int16)
        out.append(dict(path=p, dur=dur, kana=q.get('kana', ''), rate=rate, pcm=pcm))
    return out


def plan_timing(durs):
    """実測尺からシーン境界を作る。3〜9秒・全体30〜45秒に収める。"""
    spans = [round(d + GAP, 2) for d in durs]
    spans[-1] = round(durs[-1] + TAIL, 2)
    for i, s in enumerate(spans):
        if s < MIN_SCENE:
            spans[i] = MIN_SCENE
    total = round(sum(spans), 2)
    if total < MIN_TOTAL:                      # 余りを、伸ばせるシーンへ均等に足す
        need = round(MIN_TOTAL - total, 2)
        room = [MAX_SCENE - s for s in spans]
        while need > 0.009 and sum(room) > 0.009:
            per = min(need / max(1, sum(1 for r in room if r > 0.009)), 0.1)
            for i in range(len(spans)):
                if room[i] > 0.009 and need > 0.009:
                    add = min(per, room[i], need)
                    spans[i] = round(spans[i] + add, 2)
                    room[i] -= add
                    need = round(need - add, 2)
    total = round(sum(spans), 2)
    if total > MAX_TOTAL:
        raise SystemExit('実測尺が %.1f 秒で上限45秒を超える。--speed を上げるか台本を短くする' % total)
    starts, t = [], 0.0
    for s in spans:
        starts.append(round(t, 2))
        t = round(t + s, 2)
    return starts, spans, round(t, 2)


def write_json(path, data):
    """台本を書き出す。文字列だけの配列（caption / claim_ids など）は1行にまとめて、人が読みやすい形を保つ。"""
    text = json.dumps(data, ensure_ascii=False, indent=2)
    text = re.sub(r'\[\s*\n\s*((?:"(?:[^"\\]|\\.)*"\s*,?\s*\n\s*)+)\]',
                  lambda m: '[' + ', '.join(x.strip().rstrip(',') for x in m.group(1).strip().splitlines()) + ']',
                  text)
    Path(path).write_text(text + '\n', encoding='utf-8', newline='\n')


def write_timing(path, data, starts, spans, total):
    """境界を result.json に書く。検証（間隔0・最終end=duration_sec）が通るよう、前の終わり＝次の始まりにする。"""
    n = len(data['scenes'])
    for i, sc in enumerate(data['scenes']):
        sc['start'] = starts[i]
        sc['end'] = starts[i + 1] if i + 1 < n else total
    data['duration_sec'] = total
    write_json(path, data)


# ---------------------------------------------------------------- 画面

def cover(im, w, h):
    s = max(w / im.width, h / im.height)
    im2 = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.Resampling.LANCZOS)
    x = (im2.width - w) // 2
    y = (im2.height - h) // 2
    return im2.crop((x, y, x + w, y + h))


def kenburns(base, k):
    """k=0..1 でゆっくり寄る（等倍→1.06倍）。base は 1080x1920 に cover 済み。"""
    z = 1.0 + 0.06 * k
    cw, ch = W / z, H / z
    cx, cy = base.width / 2, base.height / 2
    return base.crop((round(cx - cw / 2), round(cy - ch / 2), round(cx + cw / 2), round(cy + ch / 2))).resize((W, H), Image.Resampling.BILINEAR)


def bottom_shade(im):
    """上下を暗くする（上はタイトル、下はキャプションを写真の上でも読めるように）。"""
    ov = Image.new('L', (1, H), 0)
    px = ov.load()
    assert px is not None
    for y in range(H):
        if y < H * 0.016:
            px[0, y] = 70
        elif y < H * 0.16:
            px[0, y] = int(70 * (1 - (y - H * 0.016) / (H * 0.144)))
        elif y < H * 0.45:
            px[0, y] = 0
        elif y < H * 0.72:
            px[0, y] = int(90 * (y - H * 0.45) / (H * 0.27))
        else:
            px[0, y] = int(min(210, 90 + 120 * (y - H * 0.72) / (H * 0.28)))
    mask = ov.resize((W, H))
    dark = Image.new('RGB', (W, H), (6, 9, 14))
    return Image.composite(dark, im, mask.point(lambda v: int(v * 0.92)))


def type_label(kind):
    return {'ai': 'イメージ（AI生成）', 'diagram': '模式図', 'photo': '実写',
            'illustration': 'イラスト'}.get(kind, 'イメージ')


def caption_alpha(t, scene_start, fade=0.22):
    """シーン頭だけキャプションをフェードインさせる（PRなどには適用しない）。"""
    if fade <= 0:
        return 1.0
    return max(0.0, min(1.0, (t - scene_start) / fade))


def draw_chrome(im, data, sc, conf, scene_i, kind, caption_alpha=1.0):
    """タイトル・PR・種別ラベル・キャプション・出典を焼き込む。

    PR・タイトル・種別ラベルは全フレームで完全一致させる（ステマ告示）。
    フェードするのはキャプションと出典ラベルだけ。
    """
    d = ImageDraw.Draw(im, 'RGBA')

    def a(c, al=255):
        return c + (al,)

    def ca(c, al=255):
        return c + (int(al * caption_alpha),)

    # 見出し（上。種別ラベルの下に置き、重ならないようにする）
    lines = wrap(d, data['title'], font(44, 700), 900)[:2]
    y = 206
    for ln in lines:
        d.text((540, y), ln, font=font(44, 700), fill=a(WHITE, 235), anchor='mm',
               stroke_width=5, stroke_fill=a((0, 0, 0), 150))
        y += 58
    d.line([(120, y + 16), (960, y + 16)], fill=a(GOLD, 210), width=3)

    # PR（全編。ステマ告示対応で冒頭だけにしない）
    d.rounded_rectangle((40, 96, 158, 168), 14, fill=a((0, 0, 0), 150), outline=a(GOLD, 235), width=3)
    d.text((99, 132), 'PR', font=font(42, 700), fill=a(GOLD), anchor='mm')

    # 種別（実写と混同させない）
    lab = type_label(kind)
    f = font(30, 600)
    tw = d.textlength(lab, font=f)
    d.rounded_rectangle((W - 44 - tw - 40, 108, W - 44, 160), 12, fill=a((0, 0, 0), 140))
    d.text((W - 64, 134), lab, font=f, fill=a((232, 232, 226), 235), anchor='rm')

    # キャプション（2行以内・1行14文字以内は検査済み）
    caps = [c for c in (sc.get('caption') or []) if c]
    if caps:
        box = (44, 1252, W - 44, 1252 + 96 * len(caps) + 76)
        d.rounded_rectangle(box, 22, fill=ca((8, 12, 18), 215))
        d.rounded_rectangle((box[0], box[1], box[2], box[1] + 8), 4, fill=ca(GOLD, 230))
        cy = box[1] + 20 + (96 * len(caps) + 56) / 2
        fnt = font(66, 700)
        step = 92
        y0 = cy - step * (len(caps) - 1) / 2
        for j, ln in enumerate(caps):
            d.text((540, y0 + step * j), ln, font=fnt, fill=ca((255, 253, 246), 255), anchor='mm',
                   stroke_width=4, stroke_fill=ca((0, 0, 0), 120))

        # 出典（数値を出したシーンだけ。説明欄にも同じ内容を書く）
        src = source_label(sc, conf)
        if src:
            d.text((540, box[3] - 26), src, font=font(24, 500), fill=ca(DIM, 220), anchor='mm')
    return im


def source_label(sc, conf):
    labels = conf.get('source_labels') or {}
    for cid in sc.get('claim_ids') or []:
        if cid in labels:
            return '出典: ' + labels[cid]
    return conf.get('source_fallback', '') if sc.get('claim_ids') else ''


# ---------------------------------------------------------------- 組み立て

def build_audio(segs, starts, total, work):
    rate = segs[0]['rate']
    n = int(math.ceil((total + 0.2) * rate))
    buf = np.zeros(n, np.int16)
    for seg, st in zip(segs, starts):
        off = int((st + LEAD) * rate)
        pcm = seg['pcm']
        end = min(n, off + len(pcm))
        buf[off:end] = pcm[:end - off]
    p = work / 'narration.wav'
    with wave.open(str(p), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(buf.tobytes())
    return p


def clip_cache_dir(work, name, src, nfast):
    """クリップの内容（mtime・サイズ）とフレーム数で展開先を分ける。"""
    st = src.stat()
    key = hashlib.sha256(f'{name}|{st.st_mtime_ns}|{st.st_size}|{nfast}'.encode()).hexdigest()[:12]
    return work / 'clipframes' / f'{name}_{key}'


def prepare_clip_frames(slug_dir, conf, data, work, ff):
    """シーン背景の動画（art/clip_*.mp4）を、シーン尺ぶんの連番JPEGに展開する。

    clip がシーンより長ければ頭から切り、短ければ尺に合わせて遅くする（等速のまま尺が足りない場合のみ）。
    返り値: {シーン番号(0始まり): (ディレクトリ, フレーム数)}
    """
    clips = conf.get('clips') or {}
    out = {}
    for i, sc in enumerate(data['scenes']):
        name = clips.get(str(i + 1))
        if not name:
            continue
        src = slug_dir / 'art' / ('clip_%s.mp4' % name)
        if not src.exists():
            print('[warn] クリップが無いので静止画で描く: %s（シーン%d）' % (src.name, i + 1))
            continue
        dur = sc['end'] - sc['start']
        nfast = max(1, int(round(dur * FPS)))
        d = clip_cache_dir(work, name, src, nfast)
        if d.exists() and len(list(d.glob('f_*.jpg'))) == nfast:
            out[i] = (d, nfast)
            continue
        d.mkdir(parents=True, exist_ok=True)
        for old in d.glob('f_*.jpg'):
            old.unlink()
        clip_dur = float(subprocess.run([ffprobe_bin(ff), '-v', 'error',
                                         '-show_entries', 'format=duration', '-of', 'csv=p=0', str(src)],
                                        capture_output=True, text=True).stdout.strip() or 7.0)
        rate = clip_dur / dur if clip_dur < dur else 1.0
        vf = ('scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d' % (W, H, W, H))
        if rate < 0.999:
            vf += ',setpts=PTS/%.6f' % rate
        vf += ',fps=%d,unsharp=5:5:0.6' % FPS      # 544x960 を 1080x1920 に伸ばすので、軽く輪郭を戻す
        subprocess.run([ff, '-y', '-v', 'error', '-i', str(src), '-vf', vf, '-frames:v', str(nfast),
                        '-q:v', '3', str(d / 'f_%05d.jpg')], check=True)
        out[i] = (d, nfast)
        print('クリップ %s: %.2fs のシーンへ %d フレーム（元 %.2fs）' % (name, dur, nfast, clip_dur))
    return out


def render_frames(data, bases, kinds, conf, total, work, out_mp4, ff, clipf=None):
    scenes = data['scenes']
    clipf = clipf or {}
    proc = subprocess.Popen([ff, '-y', '-v', 'warning', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                             '-s', '%dx%d' % (W, H), '-r', str(FPS), '-i', 'pipe:0',
                             '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
                             '-pix_fmt', 'yuv420p', str(out_mp4)], stdin=subprocess.PIPE)
    assert proc.stdin is not None
    nframes = int(round(total * FPS))
    for fi in range(nframes):
        t = fi / FPS
        si = 0
        for i, sc in enumerate(scenes):
            if sc['start'] <= t < sc['end']:
                si = i
        sc = scenes[si]
        dur = max(0.01, sc['end'] - sc['start'])
        k = max(0.0, min(1.0, (t - sc['start']) / dur))
        if si in clipf:                      # 動画背景（FreeVideo）。静止画の寄り引きはしない
            d, n = clipf[si]
            idx = min(n, max(1, int((t - sc['start']) * FPS) + 1))
            im = Image.open(d / ('f_%05d.jpg' % idx)).convert('RGB')
        else:
            im = kenburns(bases[si], k)
        im = bottom_shade(im)
        # シーン頭の 0.22 秒でキャプションをフェードイン（PRは常に不透明）
        cap_alpha = caption_alpha(t, sc['start'])
        im = draw_chrome(im, data, sc, conf, si, kinds[si], caption_alpha=cap_alpha)
        proc.stdin.write(im.tobytes())
    proc.stdin.close()
    proc.wait()
    if proc.returncode:
        raise SystemExit('ffmpeg の映像エンコードに失敗')


def measure_lufs(ff, path):
    """loudnorm の1パス目で、integrated loudness などの実測値を取り出す。"""
    p = subprocess.run([ff, '-hide_banner', '-nostats', '-i', str(path), '-af',
                        'loudnorm=I=-14:TP=-1.5:LRA=7:print_format=json', '-f', 'null', '-'],
                       capture_output=True, text=True, errors='replace')
    m = re.search(r'\{[^{}]*"input_i"[^{}]*\}', p.stderr, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def mux(ff, raw_mp4, narration, total, final, bgm=None):
    """ナレーションに BGM を敷いて mux する。

    bgm: {"file": 相対パス, "gain_db": -8, "start": 8.0, "fade_in": 1.0, "fade_out": 2.0,
          "duck": {"threshold": 0.05, "ratio": 4, "attack": 10, "release": 250}}

    最終音量は loudnorm の2パス目（linear=true）で合わせる。1パス目で測った値を渡すと
    「全体に一定のゲインをかける」動作になり、BGM とナレーションの相対レベルが保たれる。
    動的な loudnorm を最終段に置くと、BGM を上げたぶん全体が押し戻されて音楽が大きくならない。
    """
    if not bgm:
        chain = '[1:a]aresample=48000[nar]'
        tmp = final.with_suffix('.mix.wav')
        subprocess.run([ff, '-y', '-v', 'warning', '-i', str(raw_mp4), '-i', str(narration),
                        '-filter_complex', chain, '-map', '[nar]', '-t', '%.2f' % total,
                        '-c:a', 'pcm_s16le', '-ar', '48000', str(tmp)], check=True)
    else:
        path = ROOT / bgm['file']
        if not path.exists():
            raise SystemExit('BGM が無い: %s' % path)
        gain = 10 ** (float(bgm.get('gain_db', -8)) / 20)
        fin = float(bgm.get('fade_in', 1.0))
        fout = float(bgm.get('fade_out', 2.0))
        duck = bgm.get('duck') or {}
        thr = float(duck.get('threshold', 0.05))
        ratio = float(duck.get('ratio', 4))
        attack = float(duck.get('attack', 10))
        release = float(duck.get('release', 250))
        fc = ('[1:a]aresample=48000,atrim=start=%.3f,asetpts=N/SR/TB,volume=%.4f,'
              'afade=t=in:d=%.2f,afade=t=out:st=%.2f:d=%.2f[b];'
              '[2:a]aresample=48000,asplit=2[n1][n2];'
              '[b][n1]sidechaincompress=threshold=%.3f:ratio=%.1f:attack=%.0f:release=%.0f[bd];'
              '[bd][n2]amix=inputs=2:duration=first:normalize=0[a]'
              % (float(bgm.get('start', 0.0)), gain, fin, max(0.0, total - fout), fout,
                 thr, ratio, attack, release))
        tmp = final.with_suffix('.mix.wav')
        subprocess.run([ff, '-y', '-v', 'warning', '-i', str(raw_mp4), '-stream_loop', '-1',
                        '-i', str(path), '-i', str(narration), '-filter_complex', fc,
                        '-map', '[a]', '-t', '%.2f' % total, '-c:a', 'pcm_s16le', '-ar', '48000', str(tmp)],
                       check=True)

    m = measure_lufs(ff, tmp)
    if m:
        af = ('loudnorm=I=-14:TP=-1.5:LRA=7:measured_I=%s:measured_TP=%s:measured_LRA=%s'
              ':measured_thresh=%s:offset=%s:linear=true,alimiter=limit=0.79:level=disabled'
              % (m['input_i'], m['input_tp'], m['input_lra'], m['input_thresh'], m['target_offset']))
    else:
        af = 'loudnorm=I=-14:TP=-1.5:LRA=7,alimiter=limit=0.79:level=disabled'
    subprocess.run([ff, '-y', '-v', 'warning', '-i', str(raw_mp4), '-i', str(tmp), '-af', af,
                    '-map', '0:v', '-map', '1:a', '-t', '%.2f' % total,
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
                    '-movflags', '+faststart', str(final)], check=True)
    tmp.unlink(missing_ok=True)
    if m:
        print('ミックス: %.1f LUFS（実測）→ linear loudnorm で -14 LUFS に合わせた' % float(m['input_i']))


def subtitle_chunks(text, maxc=15, lines=2):
    parts = [p for p in re.split(r'(?<=[、。？！?!])', text) if p]
    out, cur = [], ''
    for p in parts:
        if len(cur) + len(p) <= maxc * lines:
            cur += p
        else:
            if cur:
                out.append(cur)
            cur = p
    if cur:
        out.append(cur)
    return out or [text]


def write_srt(path, data):
    def ts(x):
        ms = round(x * 1000)
        return '%02d:%02d:%02d,%03d' % (ms // 3600000, ms // 60000 % 60, ms // 1000 % 60, ms % 1000)
    rows, idx = [], 1
    for sc in data['scenes']:
        ch = subtitle_chunks(sc['narration'])
        span = sc['end'] - sc['start']
        weights = [len(c) for c in ch]
        tot = sum(weights) or 1
        t0 = sc['start']
        for c, wgt in zip(ch, weights):
            d = span * wgt / tot
            rows.append('%d\n%s --> %s\n%s' % (idx, ts(t0), ts(t0 + d), c))
            idx += 1
            t0 += d
    path.write_text('\n\n'.join(rows) + '\n', encoding='utf-8')


def visual_disclosure(data, conf):
    """実際に使った映像種別に合わせた説明欄の一文を返す。"""
    art_types = conf.get('art_types') or {}
    kinds = {art_types.get(str(i), 'ai') for i in range(1, len(data.get('scenes') or []) + 1)}
    base = '・映像はAI生成のイメージ、自作のイラスト・模式図です。実在の商品・店舗・ロゴではありません。'
    if kinds == {'photo'}:
        return '・映像は実写です。実在の商品・店舗・ロゴではありません。'
    if 'photo' in kinds:
        return base + ' 一部に実写を使用しています。'
    return base


def description(data, conf):
    claims = data.get('claims') or []
    refs = '\n'.join('・%s\n  %s' % (c['statement'], c.get('source_url') or '（AIアシスタントの回答）')
                     for c in claims)
    music = ''
    if conf.get('bgm'):
        credit = conf['bgm'].get('credit') or '魔王魂'
        music = '\n・音楽：%s' % credit
    tags = conf.get('hashtags') or '#Shorts'
    note = conf.get('description_note')
    note_block = ('\n■ 注意\n%s\n' % note) if note else ''

    # アフィリエイトリンクは説明欄の一番上（PR表記の直後）に置く。
    # render.json の "affiliate": {"label": "...", "url": "..."} で指定する。
    aff = conf.get('affiliate') or {}
    aff_url = (aff.get('url') or '').strip()
    if aff_url:
        label = aff.get('label') or '商品ページはこちら（楽天市場）'
        link_block = f'{label}\n{aff_url}\n'
    else:
        link_block = ''
    product_name = (conf.get('product_name') or '').strip()
    product_block = ('商品名：%s\n' % product_name) if product_name else ''

    return f"""【PR】この動画は楽天アフィリエイト（アフィリエイト広告）を含みます。
{product_block}{link_block}
{data['title']}

{data['hook']}

■ 動画で示した事実と出典
{refs}
{note_block}
■ 映像と音声について
{visual_disclosure(data, conf)}
・音声：VOICEVOX:{conf.get('speaker', '青山龍星')}{music}
・商品名・価格・仕様は、必ず販売元の商品ページでご確認ください。
・リンクは広告（アフィリエイト）です。購入により当チャンネルに報酬が発生します。

{tags}
"""


def fixed_comment(data, conf):
    aff = conf.get('affiliate') or {}
    aff_url = (aff.get('url') or '').strip()
    link_line = ('商品ページ：%s\n' % aff_url) if aff_url else ''
    product_name = (conf.get('product_name') or '').strip()
    name_line = ('商品名：%s\n' % product_name) if product_name else ''
    return f"""【PR】この動画はアフィリエイト広告を含みます。
{data['title']}
{name_line}{link_line}映像はAI生成のイメージ、自作のイラスト・模式図です（実在の商品ではありません）。
出典は説明欄に記載しています。
"""


def main():
    ap = argparse.ArgumentParser(description='制作標準の台本から Shorts の MP4 を作る')
    ap.add_argument('slug')
    ap.add_argument('--plan', action='store_true', help='音声を合成して実測尺を result.json に書く（描画しない）')
    ap.add_argument('--speaker')
    ap.add_argument('--speed', type=float)
    ap.add_argument('--out-dir', default='out')
    ap.add_argument('--thumb-at', type=float, default=1.2, help='サムネに使う秒')
    args = ap.parse_args()

    slug_dir = ROOT / 'shorts' / args.slug
    result = slug_dir / 'result.json'
    if not result.exists():
        raise SystemExit('台本が無い: %s' % result)
    data = load_json(result)
    conf = load_render_conf(slug_dir)
    speaker = args.speaker or conf.get('speaker', '青山龍星')
    speed = args.speed if args.speed is not None else float(conf.get('speed', 0.95))

    segs = synthesize(slug_dir, data, conf, speaker, speed)
    starts, spans, total = plan_timing([s['dur'] for s in segs])

    print('話者: %s / 話速 %.2f / 実測 %.1f 秒' % (speaker, speed, sum(s['dur'] for s in segs)))
    print('%-4s %-7s %-7s %s' % ('#', 'audio', 'scene', 'caption'))
    for i, (s, sp) in enumerate(zip(segs, spans), 1):
        print('%-4d %-7.2f %-7.2f %s' % (i, s['dur'], sp, ' / '.join(data['scenes'][i - 1]['caption'])))
    print('合計 %.2f 秒' % total)

    if args.plan:
        write_timing(result, data, starts, spans, total)
        print('\nresult.json の start/end/duration_sec を更新した。次に必ず:')
        print('  python scripts/shorts_standard.py check %s' % result)
        return

    # 描画は result.json の境界をそのまま使う（検査した内容と描画を一致させる）
    if abs((data.get('duration_sec') or 0) - total) > 0.2:
        raise SystemExit('result.json の尺（%.2f 秒）が実測（%.2f 秒）と違う。先に --plan を実行する'
                         % (data.get('duration_sec') or 0, total))

    kinds = []
    for i, sc in enumerate(data['scenes'], 1):
        p = slug_dir / 'art' / ('scene_%02d.png' % i)
        if not p.exists():
            raise SystemExit('素材が無い: %s（シーン%d）' % (p, i))
        kinds.append((conf.get('art_types') or {}).get(str(i), 'ai'))
    bases = [cover(Image.open(slug_dir / 'art' / ('scene_%02d.png' % i)).convert('RGB'), W, H)
             for i in range(1, len(data['scenes']) + 1)]

    draft = data.get('status') != 'ready'
    out_dir = ROOT / args.out_dir / ('draft' if draft else '')
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = args.slug + ('_DRAFT' if draft else '')
    mp4 = out_dir / (stem + '.mp4')
    ff = ffmpeg_bin()
    work = ROOT / 'cache' / ('render_' + args.slug)
    work.mkdir(parents=True, exist_ok=True)
    clipf = prepare_clip_frames(slug_dir, conf, data, work, ff)

    narration = build_audio(segs, starts, total, work)
    raw = work / 'raw.mp4'
    print('映像を書き出し中…（%d フレーム）' % int(round(total * FPS)))
    render_frames(data, bases, kinds, conf, total, work, raw, ff, clipf=clipf)
    mux(ff, raw, narration, total, mp4, bgm=conf.get('bgm'))
    write_srt(out_dir / (stem + '_subtitles.srt'), data)
    (out_dir / (stem + '_description.md')).write_text(description(data, conf), encoding='utf-8')
    (out_dir / (stem + '_fixed_comment.md')).write_text(fixed_comment(data, conf), encoding='utf-8')

    # サムネ（PR が入ったフレームをそのまま使う）
    thumb_t = min(max(0.0, args.thumb_at), total - 0.1)
    si = next(i for i, sc in enumerate(data['scenes']) if sc['start'] <= thumb_t < sc['end'])
    sc = data['scenes'][si]
    k = (thumb_t - sc['start']) / max(0.01, sc['end'] - sc['start'])
    if si in clipf:
        d, n = clipf[si]
        idx = min(n, max(1, int((thumb_t - sc['start']) * FPS) + 1))
        im = Image.open(d / ('f_%05d.jpg' % idx)).convert('RGB')
    else:
        im = kenburns(bases[si], k)
    im = bottom_shade(im)
    im = draw_chrome(im, data, sc, conf, si, kinds[si])
    im.save(out_dir / (stem + '_thumb.jpg'), quality=92)

    print('\n完成: %s' % mp4)
    if draft:
        print('\n【下書き】status=%s。公開しないこと。' % data.get('status'))
        for n in data.get('needs_research') or []:
            print('  未確認: %s' % n)


if __name__ == '__main__':
    main()


