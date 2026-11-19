"""peak_hours の素材6枚（1・4はFreeVideo失敗時の静止フォールバック、2・3・5・6は模式図）。"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
ART = Path('shorts/peak_hours/art')
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


def note(d, text, y=332):
    d.text((W // 2, y), text, font=font(22, 500), fill=DIM, anchor='mm')


def tag(d, xy, text, fill, size=23, anchor='mm'):
    f = font(size, 600)
    box = d.textbbox(xy, text, font=f, anchor=anchor)
    d.rounded_rectangle((box[0] - 12, box[1] - 8, box[2] + 12, box[3] + 8), 8, fill=(12, 18, 26, 225))
    d.text(xy, text, font=f, fill=fill, anchor=anchor)


def axes(d, x0=110, x1=970, y0=1160, y1=470, ylabel='需要'):
    d.line([(x0, y0), (x1, y0)], fill=DIM, width=3)
    d.line([(x0, y0), (x0, y1)], fill=DIM, width=3)
    for h in range(6, 25, 3):
        x = x0 + (h - 6) / 18 * (x1 - x0)
        d.line([(x, y0), (x, y0 + 12)], fill=DIM, width=2)
        d.text((x, y0 + 28), str(h), font=font(20, 500), fill=DIM, anchor='mm')
    d.text((x0, y1 - 28), ylabel, font=font(22, 600), fill=DIM, anchor='lm')


def hx(h, x0=110, x1=970):
    return x0 + (h - 6) / 18 * (x1 - x0)


def vy(v, y0=1160, y1=470):
    return y0 - v * (y0 - y1)


def curve(d, pts, col, width=9, x0=110, x1=970):
    xy = [(hx(h, x0, x1), vy(v)) for h, v in pts]
    d.line(xy, fill=col + (255,), width=width, joint='curve')
    for x, y in xy:
        d.ellipse((x - 5, y - 5, x + 5, y + 5), fill=col + (255,))


def band(d, h0, h1, col, x0=110, x1=970):
    d.rectangle((hx(h0, x0, x1), 470, hx(h1, x0, x1), 1160), fill=col + (34,))


def scene_01():
    """静止フォールバック：夕方のリビング。"""
    im, d = base()
    note(d, '出典：資源エネルギー庁「エネこれ」')
    d.rectangle((120, 430, 430, 830), fill=(46, 58, 78, 255))
    d.rectangle((138, 450, 412, 812), fill=(88, 76, 92, 255))
    d.polygon([(138, 690), (412, 610), (412, 812), (138, 812)], fill=(52, 62, 84, 255))
    d.ellipse((760, 430, 900, 470), fill=GOLD + (150,))
    d.line([(830, 470), (830, 560)], fill=DIM + (180,), width=4)
    d.rounded_rectangle((560, 470, 930, 540), 12, fill=(216, 222, 228, 255))
    for i in range(14):
        d.line([(585 + i * 24, 542), (585 + i * 24, 570)], fill=(180, 190, 200, 120), width=3)
    d.rounded_rectangle((160, 980, 940, 1120), 26, fill=(44, 52, 66, 255))
    d.rounded_rectangle((220, 900, 460, 1000), 20, fill=(58, 68, 84, 255))
    im.save(ART / 'scene_01.png')
    print('scene_01.png')


def scene_02():
    im, d = base()
    note(d, '出典：資源エネルギー庁「エネこれ」')
    axes(d)
    band(d, 13, 17, GOLD)
    total = [(6, .22), (9, .46), (12, .70), (14, .86), (16, .80), (18, .62), (21, .52), (24, .34)]
    home = [(6, .14), (9, .20), (12, .30), (15, .34), (18, .82), (20, .74), (22, .50), (24, .24)]
    curve(d, total, GOLD)
    curve(d, home, BLUE)
    tag(d, (300, 690), '総需要 13-17時', GOLD, size=24, anchor='lm')
    tag(d, (720, 830), '家庭 18時ごろ', BLUE, size=24, anchor='lm')
    tag(d, (540, 1290), '時間帯の山は二つ', WHITE, size=27)
    im.save(ART / 'scene_02.png')
    print('scene_02.png')


def scene_03():
    im, d = base()
    note(d, '出典：資源エネルギー庁「エネこれ」')
    axes(d)
    band(d, 13, 17, GOLD)
    total = [(6, .22), (9, .46), (12, .70), (14, .86), (16, .80), (18, .62), (21, .52), (24, .34)]
    curve(d, total, GOLD)
    tag(d, (hx(15), 640), '13:00-17:00', GOLD, size=26)
    tag(d, (540, 1290), '地域で形は少し違う', DIM, size=24)
    im.save(ART / 'scene_03.png')
    print('scene_03.png')


def scene_04():
    """静止フォールバック：夕方のキッチン。"""
    im, d = base()
    note(d, '出典：資源エネルギー庁「エネこれ」')
    d.rectangle((640, 430, 940, 820), fill=(46, 58, 78, 255))
    d.rectangle((662, 452, 918, 798), fill=(88, 76, 92, 255))
    d.polygon([(662, 700), (918, 630), (918, 798), (662, 798)], fill=(52, 62, 84, 255))
    d.rectangle((140, 900, 950, 930), fill=(96, 108, 124, 255))
    d.rounded_rectangle((250, 930, 470, 1120), 14, fill=(188, 196, 206, 255))
    d.line([(360, 950), (360, 1090)], fill=(120, 130, 142, 255), width=6)
    d.ellipse((590, 840, 790, 950), fill=(110, 120, 134, 255))
    d.rectangle((580, 950, 800, 970), fill=(150, 158, 170, 255))
    d.line([(690, 830), (690, 850)], fill=DIM + (200,), width=5)
    im.save(ART / 'scene_04.png')
    print('scene_04.png')


def scene_05():
    im, d = base()
    note(d, '出典：資源エネルギー庁「エネこれ」')
    axes(d, ylabel='発電量')
    band(d, 17, 20, BLUE)
    solar = [(6, .04), (9, .42), (12, .78), (15, .68), (17, .38), (19, .06), (21, .01), (24, .0)]
    curve(d, solar, BLUE)
    tag(d, (hx(18), 760), '17:00-20:00', BLUE, size=26)
    tag(d, (540, 1290), '夕方に発電量が下がる', WHITE, size=25)
    im.save(ART / 'scene_05.png')
    print('scene_05.png')


def scene_06():
    im, d = base()
    note(d, '出典：資源エネルギー庁「エネこれ」')
    axes(d, 110, 530)
    axes(d, 550, 970)
    band(d, 13, 17, GOLD, 110, 530)
    band(d, 17, 20, BLUE, 550, 970)
    left = [(6, .22), (12, .70), (15, .86), (18, .60), (24, .34)]
    right = [(6, .16), (12, .32), (17, .50), (19, .82), (24, .26)]
    curve(d, left, GOLD, 7, 110, 530)
    curve(d, right, BLUE, 7, 550, 970)
    tag(d, (320, 680), '総需要', GOLD, size=24)
    tag(d, (760, 680), '家庭', BLUE, size=24)
    tag(d, (540, 1300), '19時ごろ・概算・地域差', DIM, size=24)
    im.save(ART / 'scene_06.png')
    print('scene_06.png')


if __name__ == '__main__':
    ART.mkdir(parents=True, exist_ok=True)
    scene_01()
    scene_02()
    scene_03()
    scene_04()
    scene_05()
    scene_06()
