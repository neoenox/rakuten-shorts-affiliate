"""led_light の素材6枚（1・6は自作イラスト、2〜5は模式図）。字幕帯 y=1252 より上に収める。"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
ART = Path('shorts/led_light/art')
FONT = 'C:/Windows/Fonts/NotoSansJP-VF.ttf'
BG_TOP, BG_BOT = (10, 16, 24), (20, 30, 40)
GOLD = (239, 201, 118)
WHITE = (246, 244, 236)
DIM = (150, 162, 174)
BLUE = (128, 186, 236)
WARM = (236, 196, 130)
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


def scene_01():
    im, d = base()
    d.rectangle((0, 0, W, 1300), fill=(22, 28, 38))
    d.rectangle((0, 1300, W, H), fill=(34, 30, 28))
    # 天井の照明
    d.line([(540, 0), (540, 150)], fill=(120, 112, 100), width=8)
    d.polygon([(430, 150), (650, 150), (600, 230), (480, 230)], fill=(240, 214, 160))
    for r in range(420, 0, -40):
        d.ellipse((540 - r, 420 - r // 2, 540 + r, 420 + r // 2), fill=(255, 220, 160, 2))
    # 机と人物
    d.rectangle((0, 1150, W, 1300), fill=(66, 52, 44))
    d.rectangle((120, 1150, 520, 1200), fill=(120, 96, 78))
    d.ellipse((560, 900, 700, 1040), fill=(52, 48, 60))
    d.rounded_rectangle((520, 1020, 740, 1200), 60, fill=(64, 60, 74))
    d.text((W // 2, 1500), '夜の部屋', font=font(30, 600), fill=DIM, anchor='mm')
    im.save(ART / 'scene_01.png')
    print('scene_01.png')


def scene_02():
    im, d = base()
    heading(d, '54W → 7.5W', y=380, note='年間2,000時間使用の試算')
    bars = [('白熱 54W', 54, WARM), ('LED 7.5W', 7.5, BLUE)]
    base_y, scale = 980, 420 / 54
    for i, (lab, w, col) in enumerate(bars):
        h = max(28, w * scale)
        x = 320 + i * 440
        d.rounded_rectangle((x - 90, base_y - h, x + 90, base_y), 14, fill=col + (230,))
        d.text((x, base_y - h - 36), f'{w}W', font=font(40, 800), fill=col, anchor='mm')
        d.text((x, base_y + 44), lab, font=font(25, 600), fill=DIM, anchor='mm')
    d.text((W // 2, 1090), '年 約2,880円', font=font(78, 800), fill=GOLD, anchor='mm')
    d.text((W // 2, 1175), 'の差（1日およそ5.5時間）', font=font(24, 500), fill=DIM, anchor='mm')
    im.save(ART / 'scene_02.png')
    print('scene_02.png')


def scene_03():
    im, d = base()
    heading(d, '器具 68W → 34W', y=380, note='年間2,000時間使用の試算')
    bars = [('蛍光灯器具 68W', 68, WARM), ('LED器具 34W', 34, BLUE)]
    base_y, scale = 980, 420 / 68
    for i, (lab, w, col) in enumerate(bars):
        h = w * scale
        x = 320 + i * 440
        d.rounded_rectangle((x - 90, base_y - h, x + 90, base_y), 14, fill=col + (230,))
        d.text((x, base_y - h - 36), f'{w}W', font=font(40, 800), fill=col, anchor='mm')
        d.text((x, base_y + 44), lab, font=font(24, 600), fill=DIM, anchor='mm')
    d.text((W // 2, 1090), '年 約2,110円', font=font(78, 800), fill=GOLD, anchor='mm')
    im.save(ART / 'scene_03.png')
    print('scene_03.png')


def scene_04():
    im, d = base()
    heading(d, '1日1時間 短くする', y=380, note='LED器具34Wを1灯')
    x0, x1, y = 100, 980, 640
    d.rounded_rectangle((x0, y, x1, y + 130), 18, fill=(30, 46, 60), outline=(70, 86, 100), width=3)
    for i in range(1, 24):
        x = x0 + (x1 - x0) * i / 24
        d.line([(x, y), (x, y + 130)], fill=(60, 76, 92), width=2)
    cut0 = x0 + (x1 - x0) * 23 / 24
    d.rectangle((cut0, y, x1, y + 130), fill=(236, 132, 112, 220))
    d.text((W // 2, y + 200), '使っている時間のうち1時間を消す', font=font(26, 600), fill=DIM, anchor='mm')
    d.text((W // 2, 1050), '年 約380円', font=font(78, 800), fill=GOLD, anchor='mm')
    im.save(ART / 'scene_04.png')
    print('scene_04.png')


def scene_05():
    im, d = base()
    heading(d, '1日1時間だけ調光', y=380, note='50%の明るさに下げる')
    d.rounded_rectangle((140, 600, 940, 900), 24, outline=(120, 134, 148), width=6)
    d.rectangle((140, 600, 540, 900), fill=(255, 226, 150, 210))
    d.text((330, 750), '50%', font=font(64, 800), fill=(40, 40, 40), anchor='mm')
    d.text((740, 750), '残り', font=font(40, 600), fill=DIM, anchor='mm')
    d.text((W // 2, 1000), '明るさを半分にすると、消費電力も下がる', font=font(24, 500), fill=DIM, anchor='mm')
    d.text((W // 2, 1080), '年 約190円', font=font(78, 800), fill=GOLD, anchor='mm')
    im.save(ART / 'scene_05.png')
    print('scene_05.png')


def scene_06():
    im, d = base()
    # 天井のソケットだけ（商品は描かない）
    d.ellipse((420, 620, 660, 760), outline=(150, 160, 172), width=10)
    d.ellipse((470, 660, 610, 720), fill=(70, 80, 92))
    d.line([(540, 760), (540, 900)], fill=(150, 160, 172), width=8)
    d.rounded_rectangle((300, 900, 780, 1060), 20, outline=(120, 134, 148), width=5)
    d.text((540, 980), '器具の対応を確認', font=font(38, 700), fill=WHITE, anchor='mm')
    d.text((W // 2, 1140), '密閉器具・調光器に対応した製品を選ぶ', font=font(24, 500), fill=DIM, anchor='mm')
    im.save(ART / 'scene_06.png')
    print('scene_06.png')


if __name__ == '__main__':
    for fn in (scene_01, scene_02, scene_03, scene_04, scene_05, scene_06):
        fn()
