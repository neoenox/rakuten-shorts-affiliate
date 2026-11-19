"""wifi_band の素材6枚（1・4は情景フォールバック、2・3・5・6は模式図）。

動画タイトルが上部に描かれるため、図解側には見出しを置かない（2026-11-19 の実測）。
字幕帯 y=1252 より上に収める。
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
ART = Path('shorts/wifi_band/art')
FONT = 'C:/Windows/Fonts/NotoSansJP-VF.ttf'
BG_TOP, BG_BOT = (10, 16, 24), (20, 30, 40)
GOLD = (239, 201, 118)
WHITE = (246, 244, 236)
DIM = (150, 162, 174)
BLUE = (128, 186, 236)
RED = (236, 132, 112)
GREEN = (140, 210, 160)

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


def router(d, x, y, scale=1):
    w, h = int(180 * scale), int(40 * scale)
    d.rounded_rectangle((x - w // 2, y, x + w // 2, y + h), 10, fill=(214, 218, 224, 255))
    for i in range(3):
        d.line([(x - 50 + i * 50, y - 18), (x - 50 + i * 50, y - 4)], fill=(180, 190, 200, 255), width=5)


def scene_01():
    im, d = base()
    d.rectangle((0, 0, W, 1252), fill=(26, 32, 44))
    d.rectangle((0, 1080, W, 1252), fill=(58, 46, 40))
    d.rectangle((130, 900, 500, 1080), fill=(80, 62, 52, 255))
    router(d, 310, 870)
    # うっすらした電波
    for r in range(90, 330, 50):
        d.arc((310 - r, 870 - r, 310 + r, 870 + r), 200, 340, fill=BLUE + (60,), width=3)
    d.rounded_rectangle((720, 740, 860, 900), 24, fill=(60, 74, 92, 255))
    d.rectangle((738, 760, 842, 880), fill=(110, 150, 186, 255))
    d.text((W // 2, 145), '夜の部屋', font=font(28, 600), fill=DIM, anchor='mm')
    im.save(ART / 'scene_01.png')
    print('scene_01.png')


def scene_02():
    im, d = base()
    note(d, '出典：総務省 電波利用ポータル')
    boxes = [('2.4GHz', 240, BLUE), ('5GHz', 240, GOLD), ('6GHz', 200, GREEN)]
    x = 90
    for name, w, col in boxes:
        d.rounded_rectangle((x, 500, x + w, 700), 16, fill=col + (200,))
        d.text((x + w // 2, 600), name, font=font(32, 800), fill=(14, 20, 28), anchor='mm')
        x += w + 25
    # 5GHz の内訳
    d.line([(355, 700), (355, 780), (620, 780)], fill=GOLD + (180,), width=3)
    for i, lab in enumerate(['5.2', '5.3', '5.6']):
        bx = 390 + i * 100
        d.rounded_rectangle((bx, 820, bx + 86, 900), 10, fill=(60, 54, 34, 255), outline=GOLD + (255,), width=3)
        d.text((bx + 43, 860), lab, font=font(24, 700), fill=GOLD, anchor='mm')
    tag(d, (540, 1010), '5GHz は 5.2・5.3・5.6 で使用条件が違う', WHITE, size=23)
    tag(d, (540, 1100), 'まずは 2.4 か 5 を選ぶ', BLUE, size=26)
    im.save(ART / 'scene_02.png')
    print('scene_02.png')


def scene_03():
    im, d = base()
    note(d, '出典：総務省 ローカル５Ｇ等入門用資料')
    # 壁
    d.rectangle((540, 430, 600, 1140), fill=(96, 104, 118, 255))
    tag(d, (570, 1170), '壁', DIM, size=22)
    router(d, 250, 850)
    # 低い周波数：壁の裏に回り込む
    d.arc((250, 650, 950, 1250), 200, 290, fill=BLUE, width=10)
    d.line([(480, 740), (700, 700)], fill=BLUE, width=10)
    d.polygon([(700, 700), (680, 688), (680, 712)], fill=BLUE)
    tag(d, (300, 490), '低い周波数は回り込む', BLUE, size=24, anchor='lm')
    # 高い周波数：壁で減る
    d.line([(330, 950), (540, 950)], fill=RED, width=9)
    for i in range(3):
        d.line([(640 + i * 20, 920), (640 + i * 20, 980)], fill=RED + (120 - i * 35,), width=6)
    tag(d, (760, 1000), '高い周波数は回り込みが小さい', RED, size=22)
    im.save(ART / 'scene_03.png')
    print('scene_03.png')


def scene_04():
    im, d = base()
    d.rectangle((0, 0, W, 1252), fill=(30, 40, 48))
    d.rectangle((120, 200, 340, 580), fill=(170, 200, 222, 255))
    d.rectangle((760, 900, 940, 1050), fill=(74, 88, 104, 255))
    router(d, 330, 760)
    d.rounded_rectangle((700, 700, 850, 880), 24, fill=(58, 72, 88, 255))
    d.rectangle((718, 720, 832, 860), fill=(120, 160, 196, 255))
    d.arc((420, 690, 760, 900), 210, 330, fill=BLUE + (170,), width=4)
    d.text((W // 2, 145), '昼の部屋', font=font(28, 600), fill=DIM, anchor='mm')
    im.save(ART / 'scene_04.png')
    print('scene_04.png')


def scene_05():
    im, d = base()
    note(d, '出典：総務省 ローカル５Ｇ等入門用資料')
    # 重なる2つの波
    for offset, col in [(0, BLUE), (20, GOLD)]:
        pts = [(150 + i * 9, 640 - 70 * __import__('math').sin(i / 4) + offset) for i in range(75)]
        d.line(pts, fill=col, width=6)
    tag(d, (540, 470), '同じ周波数・同じタイミングで重なる → 干渉', RED, size=23)
    # 乱れた波
    pts = [(150 + i * 9, 900 + 60 * __import__('math').sin(i / 1.7) * __import__('math').sin(i / 9)) for i in range(75)]
    d.line(pts, fill=RED, width=6)
    tag(d, (540, 1040), 'ずらす：周波数 / 空間 / 時間', GREEN, size=27)
    im.save(ART / 'scene_05.png')
    print('scene_05.png')


def scene_06():
    im, d = base()
    note(d, '出典：総務省 ローカル５Ｇ等入門用資料')
    d.text((W // 2, 440), '2.4GHz のチャネル（例：1を使う場合）', font=font(28, 700), fill=WHITE, anchor='mm')
    start, bw, gap = 105, 58, 3
    for ch in range(1, 15):
        x = start + (ch - 1) * (bw + gap)
        if ch == 1:
            col, txt = GOLD, WHITE
        elif ch <= 5:
            col, txt = RED + (210,), (16, 22, 30)
        else:
            col, txt = GREEN + (220,), (16, 22, 30)
        d.rounded_rectangle((x, 560, x + bw, 660), 8, fill=col)
        d.text((x + bw // 2, 610), str(ch), font=font(26, 800), fill=txt, anchor='mm')
    tag(d, (250, 740), '2〜5 は重複', RED, size=24)
    tag(d, (740, 740), '6〜14 は重複なし', GREEN, size=24)
    d.line([(250, 780), (250, 680)], fill=RED, width=3)
    d.line([(740, 780), (740, 680)], fill=GREEN, width=3)
    tag(d, (540, 930), 'まず設定を見直す → それから中継機', WHITE, size=26)
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
