"""tv_eco_mode の素材6枚（すべて自作イラスト／模式図）。

FreeVideo (127.0.0.1:8188) が停止しているため、AGENTS.md §2 の静止フォールバックで作成。
実在の商品・ロゴ・レビュー画像は使わない。
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
ART = Path('shorts/tv_eco_mode/art')
FONT = 'C:/Windows/Fonts/NotoSansJP-VF.ttf'
BG_TOP, BG_BOT = (10, 16, 24), (20, 30, 40)
GOLD = (239, 201, 118)
WHITE = (246, 244, 236)
DIM = (150, 162, 174)
BLUE = (128, 186, 236)
GREEN = (126, 214, 160)

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


def note(d, text='出典：資源エネルギー庁「エネこれ」', y=332):
    d.text((W // 2, y), text, font=font(22, 500), fill=DIM, anchor='mm')


def tag(d, xy, text, fill, size=24, anchor='mm'):
    f = font(size, 600)
    box = d.textbbox(xy, text, font=f, anchor=anchor)
    d.rounded_rectangle((box[0] - 12, box[1] - 8, box[2] + 12, box[3] + 8), 8, fill=(12, 18, 26, 225))
    d.text(xy, text, font=f, fill=fill, anchor=anchor)


def tv(d, x, y, w, h, bright=True):
    screen = (84, 110, 140, 255) if bright else (26, 34, 46, 255)
    d.rounded_rectangle((x, y, x + w, y + h), 18, fill=(44, 52, 66, 255), outline=(120, 132, 148, 255), width=5)
    d.rectangle((x + 24, y + 24, x + w - 24, y + h - 76), fill=screen)
    d.line([(x + w // 2, y + h - 52), (x + w // 2, y + h - 22)], fill=(120, 132, 148, 255), width=7)
    d.line([(x + w // 2 - 70, y + h - 20), (x + w // 2 + 70, y + h - 20)], fill=(120, 132, 148, 255), width=7)
    if bright:
        for i in range(4):
            d.line([(x + w // 2 - 90 + i * 60, y - 34), (x + w // 2 - 70 + i * 60, y - 12)],
                   fill=GOLD + (120,), width=6)


def scene_01():
    im, d = base()
    note(d)
    tv(d, 210, 500, 660, 430, bright=True)
    tag(d, (540, 1080), '見ている時', GOLD, size=30)
    tag(d, (540, 1280), '省エネモード、効く？', WHITE, size=32)
    im.save(ART / 'scene_01.png')


def scene_02():
    im, d = base()
    note(d)
    tv(d, 90, 560, 400, 300, bright=True)
    tv(d, 590, 560, 400, 300, bright=False)
    tag(d, (290, 980), '見ている時', GOLD, size=26)
    tag(d, (790, 980), '見ていない時', BLUE, size=26)
    tag(d, (290, 1080), '省エネモード', GOLD, size=25)
    tag(d, (790, 1080), '電源オフ', BLUE, size=25)
    tag(d, (540, 1320), '資源エネルギー庁の節電Tips', DIM, size=25)
    im.save(ART / 'scene_02.png')


def scene_03():
    im, d = base()
    note(d)
    tv(d, 80, 540, 430, 320, bright=True)
    tv(d, 570, 540, 430, 320, bright=False)
    tag(d, (295, 980), '明るい', DIM, size=26)
    tag(d, (785, 980), '明るさを下げる', GREEN, size=26)
    d.rounded_rectangle((180, 1100, 400, 1150), 12, fill=(210, 220, 230, 255))
    d.rounded_rectangle((680, 1132, 900, 1150), 12, fill=GREEN + (255,))
    tag(d, (540, 1300), '消費電力も下がる', GREEN, size=30)
    im.save(ART / 'scene_03.png')


def scene_04():
    im, d = base()
    note(d)
    d.rounded_rectangle((120, 640, 960, 940), 20, fill=(44, 52, 66, 255), outline=(120, 132, 148, 255), width=5)
    d.ellipse((300, 720, 380, 800), fill=BLUE + (255,))
    d.line([(380, 760), (620, 760)], fill=BLUE + (200,), width=8)
    d.ellipse((620, 720, 700, 800), fill=(70, 80, 96, 255))
    tag(d, (340, 1040), 'つけたまま', DIM, size=27)
    tag(d, (740, 1040), '電源オフ', GREEN, size=27)
    d.line([(660, 1100), (660, 1160)], fill=(70, 80, 96, 255), width=6)
    tag(d, (540, 1300), '電気を使わない', GREEN, size=30)
    im.save(ART / 'scene_04.png')


def scene_05():
    im, d = base()
    note(d)
    d.rounded_rectangle((100, 560, 980, 760), 24, fill=GOLD + (40,), outline=GOLD + (220,), width=4)
    d.text((540, 660), '1.8% 〜 3.0%', font=font(76, 700), fill=GOLD, anchor='mm')
    tag(d, (540, 880), '19時ごろの家庭の使用量に対する概算', WHITE, size=25)
    tag(d, (540, 1010), '地域・時間帯によって変動', DIM, size=25)
    tag(d, (540, 1220), '省エネモード＋電源オフの効果', BLUE, size=27)
    im.save(ART / 'scene_05.png')


def scene_06():
    im, d = base()
    note(d)
    tv(d, 90, 560, 380, 300, bright=False)
    d.ellipse((300, 700, 350, 750), fill=GREEN + (255,))
    tag(d, (280, 940), '明るさを下げる', GREEN, size=24)
    d.rounded_rectangle((620, 620, 980, 800), 18, fill=(44, 52, 66, 255), outline=(120, 132, 148, 255), width=5)
    d.ellipse((780, 690, 840, 750), fill=(80, 90, 106, 255))
    tag(d, (800, 940), '電源を切る', GREEN, size=24)
    tag(d, (540, 1330), '19時ごろ・概算・地域差', DIM, size=25)
    im.save(ART / 'scene_06.png')


if __name__ == '__main__':
    ART.mkdir(parents=True, exist_ok=True)
    for i in range(1, 7):
        globals()['scene_%02d' % i]()
        print('scene_%02d.png' % i)
