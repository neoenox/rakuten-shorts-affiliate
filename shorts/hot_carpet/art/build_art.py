"""hot_carpet の図解素材（シーン2〜5）を作る。

  python shorts/hot_carpet/art/build_art.py
出力: scene_02.png … scene_05.png（1080x1920）。シーン1・6は生成AIのイメージ。
"""
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


def heading(d, text, y=430, size=44, note=None):
    d.text((W // 2, y), text, font=font(size, 700), fill=WHITE, anchor='mm')
    d.line([(W // 2 - 230, y + 46), (W // 2 + 230, y + 46)], fill=GOLD + (200,), width=3)
    if note:
        d.text((W // 2, y + 94), note, font=font(26, 500), fill=DIM, anchor='mm')


def scene_02():
    """ダイヤルが強→中、金額バー1本。"""
    im, d = base()
    heading(d, '「強」から「中」にすると', y=430, note='3畳用・1日5時間使用の試算')
    cx, cy, r = 540, 760, 150
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(90, 104, 118), width=10)
    d.text((cx, cy - 60), '強', font=font(64, 700), fill=(150, 120, 110), anchor='mm')
    d.line([(cx, cy + 10), (cx + 96, cy + 70)], fill=GOLD, width=12)
    d.text((cx, cy + 110), '中', font=font(52, 700), fill=GOLD, anchor='mm')
    d.text((W // 2, 1010), '年 約5,770円', font=font(96, 800), fill=GOLD, anchor='mm')
    d.text((W // 2, 1110), 'の差（同じ使い方で）', font=font(34, 500), fill=DIM, anchor='mm')
    d.rounded_rectangle((220, 1180, 860, 1224), 22, fill=GOLD + (200,))
    im.save(ART / 'scene_02.png')
    print('scene_02.png')


def scene_03():
    """3畳用と2畳用の比較。"""
    im, d = base()
    heading(d, '広さが合っていないと', y=430, note='室温20℃・1日5時間使用の試算')
    for i, (label, w, h, col) in enumerate([('3畳用', 380, 300, (150, 120, 110)), ('2畳用', 300, 240, BLUE)]):
        cx = 300 + i * 480
        x0, y0 = cx - w // 2, 700 - h // 2
        d.rounded_rectangle((x0, y0, x0 + w, y0 + h), 20, outline=col + (230,), width=8)
        d.text((cx, 700), label, font=font(40, 700), fill=col, anchor='mm')
    d.text((W // 2, 940), '3畳用を2畳の部屋で使うと', font=font(36, 600), fill=WHITE, anchor='mm')
    d.text((W // 2, 1040), '年 約2,790円の差', font=font(84, 800), fill=GOLD, anchor='mm')
    im.save(ART / 'scene_03.png')
    print('scene_03.png')


def scene_04():
    """条件パネル。"""
    im, d = base()
    heading(d, 'この金額の条件', y=430)
    items = [('室温', '20℃'), ('使用時間', '1日5時間'), ('電気料金', '31円/kWh で換算')]
    y = 560
    for name, val in items:
        d.rounded_rectangle((70, y, W - 70, y + 168), 20, fill=(24, 36, 48, 235), outline=(60, 76, 92), width=2)
        d.text((110, y + 38), name, font=font(27, 600), fill=DIM, anchor='lm')
        d.text((110, y + 100), val, font=font(40, 700), fill=WHITE, anchor='lm')
        y += 190
    d.text((W // 2, y + 30), '地域・使い方で変わります', font=font(30, 600), fill=GOLD, anchor='mm')
    d.text((W // 2, y + 80), '※ 31円/kWh は令和4年7月の新電力料金目安単価', font=font(23, 500), fill=DIM, anchor='mm')
    im.save(ART / 'scene_04.png')
    print('scene_04.png')


def scene_05():
    """直敷きと断熱マットの断面。"""
    im, d = base()
    heading(d, '床に直に敷くと、熱が逃げる', y=430, size=40)

    def panel(cx, title, with_mat):
        px0, px1 = cx - 230, cx + 230
        # カーペット
        d.rounded_rectangle((px0, 640, px1, 700), 12, fill=(150, 120, 110))
        d.text((cx, 670), 'カーペット', font=font(26, 600), fill=WHITE, anchor='mm')
        if with_mat:
            d.rounded_rectangle((px0, 700, px1, 760), 12, fill=(90, 150, 200))
            d.text((cx, 730), '断熱マット', font=font(26, 600), fill=WHITE, anchor='mm')
        # 床
        d.rectangle((px0, 760, px1, 830), fill=(70, 80, 92))
        d.text((cx, 795), '床', font=font(26, 600), fill=WHITE, anchor='mm')
        # 熱の矢印
        for k in (-1, 0, 1):
            x = cx + k * 110
            if with_mat:
                d.line([(x, 900), (x, 640)], fill=GOLD, width=9)
                d.polygon([(x, 620), (x - 20, 660), (x + 20, 660)], fill=GOLD)
            else:
                d.line([(x, 700), (x, 880)], fill=(240, 140, 110, 220), width=9)
                d.polygon([(x, 900), (x - 20, 860), (x + 20, 860)], fill=(240, 140, 110, 220))
        d.text((cx, 960), title, font=font(32, 700), fill=GOLD if with_mat else (240, 140, 110), anchor='mm')

    panel(280, '直敷き：熱が床へ', False)
    panel(800, '断熱マット：熱が上へ', True)
    d.text((W // 2, 1060), '断熱マットの効果額は公的資料に記載なし', font=font(24, 500), fill=DIM, anchor='mm')
    d.text((W // 2, 1110), '設定を1段下げて、マットで補う', font=font(30, 600), fill=WHITE, anchor='mm')
    im.save(ART / 'scene_05.png')
    print('scene_05.png')


def scene_01():
    """冬のリビング（イラスト）。人物は後ろ姿のシルエット。"""
    im, d = base()
    # 窓（寒色）
    d.rounded_rectangle((80, 430, 470, 900), 18, fill=(28, 52, 76), outline=(60, 90, 120), width=6)
    d.line([(275, 430), (275, 900)], fill=(60, 90, 120), width=4)
    d.line([(80, 665), (470, 665)], fill=(60, 90, 120), width=4)
    # ランプの光
    for r in range(320, 0, -20):
        d.ellipse((820 - r, 700 - r, 820 + r, 700 + r), fill=(255, 214, 150, max(0, 3)))
    d.line([(820, 900), (820, 1010)], fill=(120, 110, 100), width=10)
    d.polygon([(750, 900), (890, 900), (860, 820), (780, 820)], fill=(240, 210, 150))
    # 床とカーペット
    d.rectangle((0, 1010, W, H), fill=(46, 38, 34))
    d.rounded_rectangle((120, 1060, 960, 1560), 28, fill=(122, 88, 70), outline=(150, 110, 88), width=6)
    for y in range(1080, 1560, 40):
        d.line([(140, y), (940, y)], fill=(132, 96, 78), width=2)
    # 後ろ姿
    d.ellipse((430, 1120, 600, 1290), fill=(58, 54, 66))     # 頭
    d.rounded_rectangle((400, 1280, 630, 1470), 60, fill=(70, 66, 80))  # 体
    d.rounded_rectangle((360, 1160, 670, 1400), 80, fill=(96, 84, 74))  # 毛布
    # 温度計
    d.rounded_rectangle((880, 1180, 930, 1330), 20, fill=(230, 230, 226))
    d.rounded_rectangle((895, 1230, 915, 1315), 10, fill=(220, 90, 80))
    d.text((905, 1160), '室温', font=font(24, 600), fill=DIM, anchor='mm')
    im.save(ART / 'scene_01.png')
    print('scene_01.png')


def scene_06():
    """断熱マットをカーペットの下に差し込む（イラスト・断面ではなく斜め視点）。"""
    im, d = base()
    heading(d, '断熱マットを1枚', y=430, size=44, note='床からの熱逃げを減らす')
    # 床
    d.polygon([(90, 1250), (990, 1250), (900, 1350), (180, 1350)], fill=(70, 80, 92))
    # カーペット（浮かせて描く）
    d.polygon([(120, 1000), (960, 1000), (880, 1120), (200, 1120)], fill=(122, 88, 70))
    d.polygon([(120, 1000), (960, 1000), (960, 1010), (120, 1010)], fill=(150, 110, 88))
    # 差し込む断熱マット
    d.polygon([(300, 1120), (800, 1120), (740, 1180), (360, 1180)], fill=(180, 196, 208))
    d.polygon([(300, 1120), (800, 1120), (800, 1128), (300, 1128)], fill=(210, 222, 232))
    # 差し込み矢印
    d.line([(980, 1150), (760, 1150)], fill=GOLD, width=10)
    d.polygon([(730, 1150), (780, 1128), (780, 1172)], fill=GOLD)
    d.text((820, 1230), '差し込む', font=font(30, 700), fill=GOLD, anchor='mm')
    d.text((W // 2, 1420), 'カーペット', font=font(28, 600), fill=(210, 170, 150), anchor='mm')
    d.text((W // 2, 1470), '断熱マット', font=font(28, 600), fill=(200, 214, 226), anchor='mm')
    d.text((W // 2, 1520), '床', font=font(28, 600), fill=(150, 160, 172), anchor='mm')
    im.save(ART / 'scene_06.png')
    print('scene_06.png')


if __name__ == '__main__':
    scene_01()
    scene_02()
    scene_03()
    scene_04()
    scene_05()
    scene_06()
