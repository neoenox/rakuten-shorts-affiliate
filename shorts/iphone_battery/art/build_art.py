"""iphone_battery の素材（6枚）を作る。シーン1・6は自作イラスト、2〜5は模式図。"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
ART = Path(__file__).resolve().parent
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


def heading(d, text, y=430, size=42, note=None):
    d.text((W // 2, y), text, font=font(size, 700), fill=WHITE, anchor='mm')
    d.line([(W // 2 - 250, y + 46), (W // 2 + 250, y + 46)], fill=GOLD + (200,), width=3)
    if note:
        d.text((W // 2, y + 94), note, font=font(26, 500), fill=DIM, anchor='mm')


def scene_01():
    im, d = base()
    # 机
    d.rectangle((0, 1180, W, H), fill=(38, 32, 30))
    # スマホ
    d.rounded_rectangle((360, 700, 720, 1180), 46, fill=(26, 32, 40), outline=(70, 84, 100), width=6)
    d.rounded_rectangle((386, 730, 694, 1150), 30, fill=(30, 62, 92))
    # 画面の光
    for r in range(300, 0, -30):
        d.ellipse((540 - r, 940 - r, 540 + r, 940 + r), fill=(120, 180, 240, 2))
    # ケーブル
    d.line([(540, 1180), (540, 1300), (700, 1380), (900, 1380)], fill=(200, 205, 210), width=14, joint='curve')
    d.rounded_rectangle((880, 1350, 980, 1410), 12, fill=(210, 214, 218))
    d.text((540, 1680), '毎晩、充電している', font=font(30, 600), fill=DIM, anchor='mm')
    im.save(ART / 'scene_01.png')
    print('scene_01.png')


def scene_02():
    """サイクルと容量の模式図。"""
    im, d = base()
    heading(d, '充電500回で 80%', y=400, note='Appleの設計値（iPhone 14以前）')
    x0, y0, x1, y1 = 150, 620, 930, 1240
    d.line([(x0, y0), (x0, y1)], fill=(90, 104, 118), width=5)
    d.line([(x0, y1), (x1, y1)], fill=(90, 104, 118), width=5)
    for v, lab in [(100, '100%'), (80, '80%')]:
        y = y1 - (v - 70) / 40 * (y1 - y0)
        d.line([(x0 - 14, y), (x0, y)], fill=(120, 134, 148), width=4)
        d.text((x0 - 26, y), lab, font=font(28, 600), fill=DIM, anchor='rm')
    for v, lab in [(0, '0回'), (250, '250回'), (500, '500回')]:
        x = x0 + v / 500 * (x1 - x0)
        d.line([(x, y1), (x, y1 + 14)], fill=(120, 134, 148), width=4)
        d.text((x, y1 + 46), lab, font=font(28, 600), fill=DIM, anchor='mm')
    pts = [(x0, y0 + 60), (x0 + 0.25 * (x1 - x0), y0 + 120), (x0 + 0.6 * (x1 - x0), y0 + 210), (x1, y1 - (80 - 70) / 40 * (y1 - y0))]
    d.line(pts, fill=GOLD, width=8, joint='curve')
    d.ellipse((x1 - 16, pts[-1][1] - 16, x1 + 16, pts[-1][1] + 16), fill=GOLD)
    d.text((W // 2, 1360), '※ 理想的な条件下での設計値', font=font(26, 500), fill=DIM, anchor='mm')
    d.text((W // 2, 1410), '使い方で変わります', font=font(26, 500), fill=DIM, anchor='mm')
    im.save(ART / 'scene_02.png')
    print('scene_02.png')


def scene_03():
    """500回と1,000回の比較バー。"""
    im, d = base()
    heading(d, 'iPhone 15なら 1,000回', y=430, note='いずれも80%を維持する設計')
    bars = [('iPhone 14 以前', 500, GOLD), ('iPhone 15', 1000, BLUE)]
    base_y, max_h = 1180, 520
    for i, (lab, v, col) in enumerate(bars):
        h = v / 1000 * max_h
        x = 300 + i * 480
        d.rounded_rectangle((x - 90, base_y - h, x + 90, base_y), 16, fill=col + (230,))
        d.text((x, base_y - h - 40), f'{v:,}回', font=font(44, 800), fill=col, anchor='mm')
        d.text((x, base_y + 48), lab, font=font(26, 600), fill=DIM, anchor='mm')
    d.text((W // 2, 1330), 'どちらも、その回数の後も80%を保つ設計', font=font(28, 600), fill=WHITE, anchor='mm')
    im.save(ART / 'scene_03.png')
    print('scene_03.png')


def scene_04():
    """毎日1回で約500日。"""
    im, d = base()
    heading(d, '毎日1回なら 約500日', y=430, note='単純計算。実際のサイクルは残量で変わる')
    cols, rows = 10, 5
    cell, gap = 78, 10
    ox = (W - (cols * cell + (cols - 1) * gap)) // 2
    oy = 640
    for r in range(rows):
        for c in range(cols):
            x = ox + c * (cell + gap)
            y = oy + r * (cell + gap)
            filled = (r * cols + c) < 42
            d.rounded_rectangle((x, y, x + cell, y + cell), 10,
                                fill=(GOLD + (200,)) if filled else (26, 38, 50, 220),
                                outline=(70, 86, 100), width=2)
    d.text((W // 2, oy + rows * (cell + gap) + 60), '約1年4か月', font=font(80, 800), fill=GOLD, anchor='mm')
    im.save(ART / 'scene_04.png')
    print('scene_04.png')


def scene_05():
    """熱で劣化が進む。"""
    im, d = base()
    heading(d, '熱は劣化を早める', y=430, note='直射日光・高温での充電を避ける')
    # 温度計
    cx = 300
    d.rounded_rectangle((cx - 40, 620, cx + 40, 1180), 40, fill=(230, 230, 226))
    d.rounded_rectangle((cx - 22, 800, cx + 22, 1180), 22, fill=RED)
    d.ellipse((cx - 66, 1130, cx + 66, 1262), fill=RED)
    for i, v in enumerate([120, 100, 80, 60, 40, 20]):
        y = 700 + i * 70
        d.line([(cx + 52, y), (cx + 84, y)], fill=(150, 162, 174), width=4)
    d.text((cx, 1320), '高温', font=font(32, 700), fill=RED, anchor='mm')
    # 矢印（劣化が加速）
    for i in range(3):
        x = 620 + i * 120
        d.line([(x, 900), (x, 700)], fill=GOLD, width=10)
        d.polygon([(x, 670), (x - 22, 716), (x + 22, 716)], fill=GOLD)
    d.text((830, 980), '劣化が進む', font=font(34, 700), fill=GOLD, anchor='mm')
    d.text((W // 2, 1430), 'バッテリーは消耗品', font=font(30, 600), fill=DIM, anchor='mm')
    im.save(ART / 'scene_05.png')
    print('scene_05.png')


def scene_06():
    """バッグの中のモバイルバッテリー（イラスト）。"""
    im, d = base()
    # バッグ
    d.rounded_rectangle((220, 760, 860, 1400), 40, fill=(52, 46, 44), outline=(96, 84, 78), width=8)
    d.arc((400, 660, 680, 860), 200, 340, fill=(150, 140, 130), width=16)
    # モバイルバッテリー
    d.rounded_rectangle((360, 980, 660, 1220), 24, fill=(200, 205, 212), outline=(230, 234, 238), width=4)
    for i in range(4):
        d.rounded_rectangle((392 + i * 58, 1160, 428 + i * 58, 1180), 6, fill=(120, 190, 140))
    # ケーブル
    d.line([(660, 1100), (760, 1100), (800, 1240)], fill=(210, 214, 218), width=12, joint='curve')
    d.text((W // 2, 1520), '予備があると安心', font=font(32, 600), fill=DIM, anchor='mm')
    im.save(ART / 'scene_06.png')
    print('scene_06.png')


if __name__ == '__main__':
    for fn in (scene_01, scene_02, scene_03, scene_04, scene_05, scene_06):
        fn()
