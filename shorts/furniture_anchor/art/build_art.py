"""furniture_anchor の素材6枚（1・6は情景の静止画フォールバック、2〜5は模式図）。

字幕帯（y=1252 以降）には置かない。情景は FreeVideo のクリップが優先される。
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
ART = Path('shorts/furniture_anchor/art')
FONT = 'C:/Windows/Fonts/NotoSansJP-VF.ttf'
BG_TOP, BG_BOT = (10, 16, 24), (20, 30, 40)
GOLD = (239, 201, 118)
WHITE = (246, 244, 236)
DIM = (150, 162, 174)
BLUE = (128, 186, 236)
WARM = (236, 196, 130)
RED = (236, 132, 112)
GREEN = (140, 210, 160)
WOOD = (150, 112, 78)
WALL = (70, 82, 96)

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


def heading(d, text, y=340, size=42, note=None):
    d.text((W // 2, y), text, font=font(size, 700), fill=WHITE, anchor='mm')
    d.line([(W // 2 - 260, y + 50), (W // 2 + 260, y + 50)], fill=GOLD + (200,), width=3)
    if note:
        d.text((W // 2, y + 100), note, font=font(24, 500), fill=DIM, anchor='mm')


def note(d, text, y=332):
    d.text((W // 2, y), text, font=font(22, 500), fill=DIM, anchor='mm')


def shelf(d, x0, y0, x1, y1, col=WOOD):
    d.rounded_rectangle((x0, y0, x1, y1), 12, fill=col + (235,), outline=(110, 82, 58, 255), width=4)
    # 棚板
    for i in range(1, 4):
        y = y0 + (y1 - y0) * i / 4
        d.line([(x0 + 16, y), (x1 - 16, y)], fill=(96, 72, 52, 255), width=6)


def person_free_note(d, y=1150):
    d.text((W // 2, y), '実在の商品・人物は描かない（イメージ）', font=font(22, 500), fill=DIM, anchor='mm')


def scene_01():
    im, d = base()
    d.rectangle((0, 0, W, 1252), fill=(24, 30, 40))
    d.rectangle((0, 1050, W, 1252), fill=(52, 44, 40))
    # 壁と天井
    d.rectangle((0, 150, W, 1050), fill=(38, 44, 54))
    d.rectangle((0, 150, W, 170), fill=(58, 64, 74))
    # 本棚
    shelf(d, 250, 380, 830, 1050)
    # 突っ張り棒 1本
    d.rectangle((536, 170, 556, 380), fill=(190, 196, 204, 255))
    d.rectangle((520, 360, 572, 392), fill=(150, 158, 168, 255))
    # ランプの灯り
    d.ellipse((900, 760, 1010, 870), fill=(248, 216, 150, 235))
    d.polygon([(940, 700), (970, 700), (985, 762), (925, 762)], fill=(90, 84, 76, 255))
    d.text((W // 2, 145), '夜の部屋', font=font(28, 600), fill=DIM, anchor='mm')
    person_free_note(d)
    im.save(ART / 'scene_01.png')
    print('scene_01.png')


def scene_02():
    im, d = base()
    note(d, '東京消防庁ハンドブック（令和6年1月）／地震ごとに条件が異なる')
    rows = [
        ('宮城県北部地震', 49.4),
        ('岩手・宮城内陸地震', 44.6),
        ('新潟県中越地震', 41.2),
        ('新潟県中越沖地震', 40.7),
        ('熊本地震（高層）', 40.0),
        ('十勝沖地震', 36.3),
        ('福岡県西方沖地震', 36.0),
        ('能登半島地震', 29.4),
        ('熊本地震（一般住宅）', 29.2),
    ]
    top, left, bar_w = 470, 470, 470
    step = 76
    for i, (name, pct) in enumerate(rows):
        y = top + i * step
        d.text((left - 24, y), name, font=font(25, 500), fill=WHITE, anchor='rm')
        w = pct / 50 * bar_w
        d.rounded_rectangle((left, y - 20, left + bar_w, y + 20), 8, fill=(34, 46, 60, 255))
        d.rounded_rectangle((left, y - 20, left + w, y + 20), 8, fill=BLUE + (220,))
        d.text((left + w + 16, y), f'{pct}%', font=font(26, 700), fill=WHITE, anchor='lm')
    # 全体の帯
    y = top + len(rows) * step + 40
    d.rounded_rectangle((150, y - 34, 930, y + 34), 12, fill=(60, 48, 24, 255), outline=GOLD + (220,), width=3)
    d.text((W // 2, y), '近年の地震では 約30〜50%', font=font(36, 800), fill=GOLD, anchor='mm')
    im.save(ART / 'scene_02.png')
    print('scene_02.png')


def tag(d, xy, text, fill, anchor='lm', size=24):
    """背景付きの注記。図の上でも読めるようにする。"""
    f = font(size, 600)
    box = d.textbbox(xy, text, font=f, anchor=anchor)
    d.rounded_rectangle((box[0] - 12, box[1] - 8, box[2] + 12, box[3] + 8), 8, fill=(12, 18, 26, 225))
    d.text(xy, text, font=f, fill=fill, anchor=anchor)


def scene_03():
    im, d = base()
    note(d, '震度6強の揺れを再現した実験（東京消防庁）')
    # 壁と間柱
    d.rectangle((820, 420, 980, 1190), fill=WALL + (255,))
    d.rectangle((870, 420, 900, 1190), fill=(104, 116, 132, 255))
    tag(d, (900, 446), '壁下地（柱・間柱）', DIM, anchor='mm', size=22)
    # 家具
    d.rectangle((220, 620, 820, 1190), fill=WOOD + (240,))
    d.line([(220, 620), (820, 620)], fill=(110, 82, 58, 255), width=6)
    tag(d, (520, 1218), '家具（本棚など）', DIM, anchor='mm', size=22)
    # L型金具（下向き）: 壁側の縦板 + 家具天板に乗る横板
    d.rectangle((804, 520, 824, 606), fill=GOLD + (255,))
    d.rectangle((700, 600, 824, 618), fill=GOLD + (255,))
    # ネジ（壁側・家具側）
    d.line([(884, 548), (884, 588)], fill=WHITE, width=8)
    d.line([(748, 596), (748, 646)], fill=WHITE, width=8)
    tag(d, (430, 470), '壁に穴を開けられる場合', WHITE, anchor='lm', size=22)
    tag(d, (430, 520), 'L型金具（下向き）', GOLD, anchor='lm')
    d.line([(700, 512), (760, 545)], fill=GOLD + (200,), width=3)
    tag(d, (430, 700), '木ネジは長めに、\n下地まで届かせる', WHITE, anchor='lm', size=23)
    d.line([(690, 706), (740, 640)], fill=WHITE + (140,), width=3)
    # 補強板（天板に強度が無い場合の例。破線で示す）
    for x in range(250, 690, 40):
        d.line([(x, 580), (x + 22, 580)], fill=(196, 160, 110, 200), width=8)
    tag(d, (430, 900), '天板に強度が無い家具は\n幅全体に板を渡して補強', DIM, anchor='lm', size=22)
    im.save(ART / 'scene_03.png')
    print('scene_03.png')


def scene_04():
    im, d = base()
    note(d, '併用して強くなる')
    cols = [
        ('突っ張り棒のみ', '単独は効果が小さい', RED, False, False),
        ('＋粘着マット', '併用で効果が高い', GREEN, True, False),
        ('＋ストッパー', '併用で効果が高い', GREEN, False, True),
    ]
    for i, (title, verdict, col, mat, stop) in enumerate(cols):
        cx = 70 + i * 330
        w = 280
        top, bot = 470, 1040
        d.text((cx + w // 2, 420), title, font=font(25, 700), fill=WHITE, anchor='mm')
        d.rectangle((cx, top, cx + w, bot), fill=(28, 36, 48, 255), outline=(52, 66, 82, 255), width=3)
        d.line([(cx + 24, top + 34), (cx + w - 24, top + 34)], fill=(120, 132, 146), width=8)  # 天井
        d.rectangle((cx + 70, top + 170, cx + 210, bot - 40), fill=WOOD + (240,))            # 家具
        d.rectangle((cx + 133, top + 34, cx + 147, top + 170), fill=(190, 196, 204, 255))     # 棒
        if mat:
            d.rectangle((cx + 64, bot - 56, cx + 216, bot - 34), fill=BLUE + (230,))
            tag(d, (cx + 140, bot - 80), 'マット', BLUE, anchor='mm', size=20)
        if stop:
            d.polygon([(cx + 70, bot - 40), (cx + 130, bot - 40), (cx + 70, bot - 86)], fill=GOLD)
            tag(d, (cx + 190, bot - 96), 'ストッパー', GOLD, anchor='mm', size=20)
        d.text((cx + w // 2, bot + 40), verdict, font=font(23, 700), fill=col, anchor='mm')
    d.text((W // 2, 1170), '背の高い家具は、単独では効果が小さい', font=font(25, 600), fill=GOLD, anchor='mm')
    im.save(ART / 'scene_04.png')
    print('scene_04.png')


def scene_05():
    im, d = base()
    note(d, 'ポール式（突っ張り棒）の場合')
    d.rectangle((140, 430, 940, 466), fill=(86, 98, 112, 255))
    tag(d, (540, 392), '天井は材質ではなく、設置箇所の強度を確認', GOLD, anchor='mm', size=22)
    d.rectangle((300, 520, 780, 1080), fill=WOOD + (240,))
    for i in range(1, 4):
        y = 520 + (1080 - 520) * i / 4
        d.line([(316, y), (764, y)], fill=(96, 72, 52, 255), width=6)
    for x in (322, 758):
        d.rectangle((x - 8, 466, x + 8, 520), fill=(190, 196, 204, 255))
    d.line([(540, 760), (540, 600)], fill=BLUE, width=6)
    d.polygon([(540, 584), (528, 610), (552, 610)], fill=BLUE)
    tag(d, (576, 700), '壁側の奥', BLUE, anchor='lm', size=23)
    d.line([(566, 706), (546, 706)], fill=BLUE + (160,), width=3)
    d.text((W // 2, 1128), '両端の側板部に・上はポール、下はストッパーやマット', font=font(24, 700), fill=WHITE, anchor='mm')
    d.text((W // 2, 1178), '奥行きのない家具・天井との間隔が大きい場合は不向き', font=font(21, 500), fill=DIM, anchor='mm')
    im.save(ART / 'scene_05.png')
    print('scene_05.png')


def scene_06():
    im, d = base()
    d.rectangle((0, 0, W, 1252), fill=(30, 38, 48))
    d.rectangle((0, 1050, W, 1252), fill=(96, 84, 70))
    # 窓の光
    d.rectangle((60, 220, 300, 640), fill=(120, 150, 176, 255))
    d.rectangle((80, 240, 280, 620), fill=(180, 206, 226, 255))
    # 本棚
    shelf(d, 380, 360, 900, 1050)
    # 背面のL字金具
    d.line([(880, 380), (940, 380)], fill=GOLD, width=12)
    d.line([(940, 380), (940, 420)], fill=GOLD, width=12)
    # 粘着マット
    d.rectangle((390, 1032, 890, 1052), fill=BLUE + (220,))
    # ストッパー
    d.polygon([(400, 1050), (470, 1050), (400, 1030)], fill=GOLD)
    d.text((W // 2, 145), '昼の部屋', font=font(28, 600), fill=DIM, anchor='mm')
    person_free_note(d)
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
