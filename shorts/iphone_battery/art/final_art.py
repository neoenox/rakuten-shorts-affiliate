"""iphone_battery の図解（シーン2〜7）を、字幕帯 y=1252 より上に収めて描く。"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
ART = Path('shorts/iphone_battery/art')
FONT = 'C:/Windows/Fonts/NotoSansJP-VF.ttf'
BG_TOP, BG_BOT = (10, 16, 24), (20, 30, 40)
GOLD = (239, 201, 118)
WHITE = (246, 244, 236)
DIM = (150, 162, 174)
BLUE = (128, 186, 236)
RED = (236, 132, 112)

_f = {}


def font(size, weight=600):
    k = (size, weight)
    if k not in _f:
        f = ImageFont.truetype(FONT, size)
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass
        _f[k] = f
    return _f[k]


def base():
    im = Image.new('RGB', (W, H), BG_TOP)
    d = ImageDraw.Draw(im)
    for y in range(H):
        r = y / H
        d.line([(0, y), (W, y)], fill=tuple(round(BG_TOP[i] + (BG_BOT[i] - BG_TOP[i]) * r) for i in range(3)))
    for x in range(0, W, 60):
        d.line([(x, 0), (x, H)], fill=(22, 34, 46), width=1)
    for y in range(0, H, 60):
        d.line([(0, y), (W, y)], fill=(22, 34, 46), width=1)
    return im, ImageDraw.Draw(im, 'RGBA')


def heading(d, text, y=380, size=40, note=None):
    d.text((W // 2, y), text, font=font(size, 700), fill=WHITE, anchor='mm')
    d.line([(W // 2 - 250, y + 46), (W // 2 + 250, y + 46)], fill=GOLD + (200,), width=3)
    if note:
        d.text((W // 2, y + 92), note, font=font(24, 500), fill=DIM, anchor='mm')


def scene_02():
    """500回で80%の設計（模式図）。"""
    im, d = base()
    heading(d, '500回の後も 80%', y=360, note='理想的な条件下での設計値（iPhone 14以前）')
    x0, y0, x1, y1 = 150, 560, 930, 1080
    d.line([(x0, y0), (x0, y1)], fill=(90, 104, 118), width=5)
    d.line([(x0, y1), (x1, y1)], fill=(90, 104, 118), width=5)
    for v, lab in [(100, '100%'), (80, '80%')]:
        y = y1 - (v - 70) / 40 * (y1 - y0)
        d.line([(x0 - 14, y), (x0, y)], fill=(120, 134, 148), width=4)
        d.text((x0 - 26, y), lab, font=font(26, 600), fill=DIM, anchor='rm')
    for v, lab in [(0, '0回'), (250, '250回'), (500, '500回')]:
        x = x0 + v / 500 * (x1 - x0)
        d.line([(x, y1), (x, y1 + 14)], fill=(120, 134, 148), width=4)
        d.text((x, y1 + 44), lab, font=font(26, 600), fill=DIM, anchor='mm')
    y80 = y1 - (80 - 70) / 40 * (y1 - y0)
    d.line([(x0, y0 + 40), (x0 + 0.35 * (x1 - x0), y0 + 110), (x1, y80)], fill=GOLD, width=9, joint='curve')
    d.ellipse((x1 - 16, y80 - 16, x1 + 16, y80 + 16), fill=GOLD)
    d.text((W // 2, 1150), '回数は「劣化が始まる境界」ではない', font=font(26, 600), fill=DIM, anchor='mm')
    im.save(ART / 'scene_02.png')
    print('scene_02.png')


def scene_03():
    """充電サイクルの定義（50%×2＝1サイクル）。"""
    im, d = base()
    heading(d, 'サイクルは合計100%で1回', y=380, note='Appleの説明より')
    d.rounded_rectangle((120, 560, 500, 800), 24, outline=(120, 200, 150), width=6)
    d.rounded_rectangle((120, 560, 310, 800), 24, fill=(120, 200, 150, 200))
    d.text((310, 860), '50%使う', font=font(30, 700), fill=(150, 210, 170), anchor='mm')
    d.rounded_rectangle((580, 560, 960, 800), 24, outline=(120, 200, 150), width=6)
    d.rounded_rectangle((580, 560, 770, 800), 24, fill=(120, 200, 150, 200))
    d.text((770, 860), 'さらに50%', font=font(30, 700), fill=(150, 210, 170), anchor='mm')
    d.text((W // 2, 940), '↓  合わせて 100%', font=font(34, 700), fill=WHITE, anchor='mm')
    d.text((W // 2, 1030), '＝ 1サイクル', font=font(64, 800), fill=GOLD, anchor='mm')
    d.text((W // 2, 1120), '100%を1回使うのと同じ', font=font(26, 500), fill=DIM, anchor='mm')
    im.save(ART / 'scene_03.png')
    print('scene_03.png')


def scene_04():
    """500回と1,000回の比較。"""
    im, d = base()
    heading(d, 'iPhone 15なら 1,000回', y=400, note='いずれも80%を維持する設計')
    bars = [('iPhone 14 以前', 500, GOLD), ('iPhone 15', 1000, BLUE)]
    base_y, max_h = 1040, 420
    for i, (lab, v, col) in enumerate(bars):
        h = v / 1000 * max_h
        x = 320 + i * 440
        d.rounded_rectangle((x - 85, base_y - h, x + 85, base_y), 14, fill=col + (230,))
        d.text((x, base_y - h - 36), f'{v:,}回', font=font(40, 800), fill=col, anchor='mm')
        d.text((x, base_y + 44), lab, font=font(25, 600), fill=DIM, anchor='mm')
    d.text((W // 2, 1140), 'どちらも、その回数の後も80%を保つ設計', font=font(26, 600), fill=WHITE, anchor='mm')
    im.save(ART / 'scene_04.png')
    print('scene_04.png')


def scene_05():
    """毎日1サイクルで約500日。"""
    im, d = base()
    heading(d, '毎日1サイクルなら 約500日', y=380, note='1日1サイクルと仮定した単純計算')
    cols, rows, cell, gap = 10, 5, 74, 10
    ox = (W - (cols * cell + (cols - 1) * gap)) // 2
    oy = 570
    for r in range(rows):
        for c in range(cols):
            x = ox + c * (cell + gap)
            y = oy + r * (cell + gap)
            filled = (r * cols + c) < 42
            d.rounded_rectangle((x, y, x + cell, y + cell), 10,
                                fill=(GOLD + (200,)) if filled else (26, 38, 50, 220),
                                outline=(70, 86, 100), width=2)
    d.text((W // 2, oy + rows * (cell + gap) + 70), 'およそ1年4か月', font=font(70, 800), fill=GOLD, anchor='mm')
    im.save(ART / 'scene_05.png')
    print('scene_05.png')


def scene_06():
    """高温が劣化を早める。"""
    im, d = base()
    heading(d, '劣化を早める要因は高温', y=380, note='直射日光・高温での充電を避ける')
    cx = 300
    d.rounded_rectangle((cx - 38, 600, cx + 38, 1080), 36, fill=(230, 230, 226))
    d.rounded_rectangle((cx - 20, 780, cx + 20, 1080), 20, fill=RED)
    d.ellipse((cx - 62, 1040, cx + 62, 1164), fill=RED)
    for i in range(6):
        y = 670 + i * 66
        d.line([(cx + 50, y), (cx + 80, y)], fill=(150, 162, 174), width=4)
    d.text((cx, 1200 + 0), '', font=font(20))
    for i in range(3):
        x = 620 + i * 118
        d.line([(x, 900), (x, 700)], fill=GOLD, width=10)
        d.polygon([(x, 672), (x - 22, 716), (x + 22, 716)], fill=GOLD)
    d.text((830, 960), '劣化が進む', font=font(32, 700), fill=GOLD, anchor='mm')
    d.text((W // 2, 1150), 'バッテリーは消耗品', font=font(28, 600), fill=DIM, anchor='mm')
    im.save(ART / 'scene_06.png')
    print('scene_06.png')


def scene_07():
    """予備の充電手段（イラスト）。"""
    im, d = base()
    d.rounded_rectangle((220, 700, 860, 1150), 40, fill=(52, 46, 44), outline=(96, 84, 78), width=8)
    d.arc((400, 610, 680, 800), 200, 340, fill=(150, 140, 130), width=14)
    d.rounded_rectangle((360, 820, 660, 1030), 22, fill=(200, 205, 212), outline=(230, 234, 238), width=4)
    for i in range(4):
        d.rounded_rectangle((392 + i * 58, 990, 428 + i * 58, 1008), 6, fill=(120, 190, 140))
    d.line([(660, 920), (760, 920), (800, 1050)], fill=(210, 214, 218), width=12, joint='curve')
    d.text((W // 2, 1180), '予備があると安心', font=font(28, 600), fill=DIM, anchor='mm')
    im.save(ART / 'scene_07.png')
    print('scene_07.png')


if __name__ == '__main__':
    scene_02(); scene_03(); scene_04(); scene_05(); scene_06(); scene_07()
