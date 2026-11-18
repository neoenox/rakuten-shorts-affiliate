"""led_light の図解を、条件（1個あたり・器具・1灯）と確認3点を入れて描き直す。"""
import json
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


def heading(d, text, y=370, size=40, note=None):
    d.text((W // 2, y), text, font=font(size, 700), fill=WHITE, anchor='mm')
    d.line([(W // 2 - 250, y + 46), (W // 2 + 250, y + 46)], fill=GOLD + (200,), width=3)
    if note:
        d.text((W // 2, y + 92), note, font=font(23, 500), fill=DIM, anchor='mm')


def scene_02():
    im, d = base()
    heading(d, '白熱1個 → LED', y=370, note='1個あたり・年間2,000時間使用')
    bars = [('白熱 54W', 54, WARM), ('LED 7.5W', 7.5, BLUE)]
    base_y, scale = 950, 400 / 54
    for i, (lab, w, col) in enumerate(bars):
        h = max(26, w * scale)
        x = 320 + i * 440
        d.rounded_rectangle((x - 90, base_y - h, x + 90, base_y), 14, fill=col + (230,))
        d.text((x, base_y - h - 34), f'{w}W', font=font(38, 800), fill=col, anchor='mm')
        d.text((x, base_y + 42), lab, font=font(24, 600), fill=DIM, anchor='mm')
    d.text((W // 2, 1050), '年 約2,880円', font=font(76, 800), fill=GOLD, anchor='mm')
    d.text((W // 2, 1130), '電球1個の差（1日およそ5.5時間）', font=font(23, 500), fill=DIM, anchor='mm')
    im.save(ART / 'scene_02.png')
    print('scene_02.png')


def scene_03():
    im, d = base()
    heading(d, '器具ごと交換', y=370, note='年間2,000時間使用・器具1台')
    bars = [('蛍光灯器具 68W', 68, WARM), ('LED器具 34W', 34, BLUE)]
    base_y, scale = 950, 400 / 68
    for i, (lab, w, col) in enumerate(bars):
        h = w * scale
        x = 320 + i * 440
        d.rounded_rectangle((x - 90, base_y - h, x + 90, base_y), 14, fill=col + (230,))
        d.text((x, base_y - h - 34), f'{w}W', font=font(38, 800), fill=col, anchor='mm')
        d.text((x, base_y + 42), lab, font=font(22, 600), fill=DIM, anchor='mm')
    d.text((W // 2, 1050), '年 約2,110円', font=font(76, 800), fill=GOLD, anchor='mm')
    d.text((W // 2, 1130), '電球ではなく器具を入れ替える', font=font(23, 500), fill=DIM, anchor='mm')
    im.save(ART / 'scene_03.png')
    print('scene_03.png')


def scene_04():
    im, d = base()
    heading(d, 'LED器具を1日1時間', y=370, note='34W・1灯の試算')
    x0, x1, y = 100, 980, 620
    d.rounded_rectangle((x0, y, x1, y + 130), 18, fill=(30, 46, 60), outline=(70, 86, 100), width=3)
    for i in range(1, 24):
        x = x0 + (x1 - x0) * i / 24
        d.line([(x, y), (x, y + 130)], fill=(60, 76, 92), width=2)
    cut0 = x0 + (x1 - x0) * 23 / 24
    d.rectangle((cut0, y, x1, y + 130), fill=(236, 132, 112, 220))
    d.text((W // 2, y + 190), '使っている時間のうち1時間を消す', font=font(25, 600), fill=DIM, anchor='mm')
    d.text((W // 2, 1000), '年 約380円', font=font(76, 800), fill=GOLD, anchor='mm')
    d.text((W // 2, 1080), '電球形LEDランプ（7.5W）ではない', font=font(23, 500), fill=RED, anchor='mm')
    im.save(ART / 'scene_04.png')
    print('scene_04.png')


def scene_05():
    im, d = base()
    heading(d, 'LED器具を1日1時間調光', y=370, note='34W・1灯を50%にする')
    d.rounded_rectangle((140, 580, 940, 880), 24, outline=(120, 134, 148), width=6)
    d.rectangle((140, 580, 540, 880), fill=(255, 226, 150, 210))
    d.text((330, 730), '50%', font=font(60, 800), fill=(40, 40, 40), anchor='mm')
    d.text((740, 730), '残り', font=font(38, 600), fill=DIM, anchor='mm')
    d.text((W // 2, 960), '明るさを半分にすると消費電力も下がる', font=font(23, 500), fill=DIM, anchor='mm')
    d.text((W // 2, 1040), '年 約190円', font=font(76, 800), fill=GOLD, anchor='mm')
    d.text((W // 2, 1120), '調光機能のある器具で', font=font(23, 500), fill=DIM, anchor='mm')
    im.save(ART / 'scene_05.png')
    print('scene_05.png')


def scene_06():
    im, d = base()
    heading(d, '交換前の3つの確認', y=380, size=38)
    items = [('口金のサイズ', 'E26・E17 など'), ('密閉器具', '対応品を選ぶ'), ('調光器', '対応品を選ぶ')]
    y = 560
    for head, sub in items:
        d.rounded_rectangle((90, y, W - 90, y + 170), 20, fill=(24, 36, 48, 235), outline=(60, 76, 92), width=2)
        d.rounded_rectangle((120, y + 50, 180, y + 110), 10, outline=GOLD, width=4)
        d.text((210, y + 62), head, font=font(34, 700), fill=WHITE, anchor='lm')
        d.text((210, y + 118), sub, font=font(24, 500), fill=DIM, anchor='lm')
        y += 190
    d.text((W // 2, y + 30), '合わないと点かない・壊れることがある', font=font(26, 600), fill=RED, anchor='mm')
    im.save(ART / 'scene_06.png')
    print('scene_06.png')


if __name__ == '__main__':
    scene_02(); scene_03(); scene_04(); scene_05(); scene_06()
