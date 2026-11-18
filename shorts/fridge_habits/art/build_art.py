"""fridge_habits の素材（6枚）。シーン1は自作イラスト、2〜6は模式図。"""
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


def heading(d, text, y=400, size=40, note=None):
    d.text((W // 2, y), text, font=font(size, 700), fill=WHITE, anchor='mm')
    d.line([(W // 2 - 250, y + 46), (W // 2 + 250, y + 46)], fill=GOLD + (200,), width=3)
    if note:
        d.text((W // 2, y + 94), note, font=font(25, 500), fill=DIM, anchor='mm')


def money(d, text, y, color=GOLD, size=84):
    d.text((W // 2, y), text, font=font(size, 800), fill=color, anchor='mm')


def scene_01():
    im, d = base()
    d.rectangle((0, 0, W, 1280), fill=(22, 28, 38))
    d.rectangle((0, 1280, W, H), fill=(34, 30, 28))
    # 冷蔵庫
    d.rounded_rectangle((520, 420, 960, 1300), 20, fill=(226, 230, 236), outline=(196, 202, 210), width=5)
    d.line([(520, 700), (960, 700)], fill=(180, 188, 198), width=6)
    # 開いた扉と光
    d.polygon([(520, 420), (300, 480), (300, 1240), (520, 1300)], fill=(240, 226, 170, 90))
    d.rounded_rectangle((900, 560, 930, 660), 12, fill=(180, 188, 198))
    # 人物（後ろ姿）
    d.ellipse((180, 780, 320, 920), fill=(52, 48, 60))
    d.rounded_rectangle((140, 900, 360, 1180), 60, fill=(64, 60, 74))
    d.text((W // 2, 1580), '夜のキッチン', font=font(30, 600), fill=DIM, anchor='mm')
    im.save(ART / 'scene_01.png')
    print('scene_01.png')


def scene_02():
    im, d = base()
    heading(d, '設定を「中」から「弱」へ', y=380, note='年間の差（公的資料の試算）')
    cx, cy, r = 540, 700, 140
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(90, 104, 118), width=10)
    d.text((cx - 60, cy - 40), '中', font=font(56, 700), fill=DIM, anchor='mm')
    d.line([(cx, cy + 20), (cx + 72, cy + 72)], fill=GOLD, width=12)
    d.text((cx + 30, cy + 96), '弱', font=font(48, 700), fill=GOLD, anchor='mm')
    money(d, '年 約1,970円', 1080)
    d.text((W // 2, 1220), '※ 食品の傷みに注意', font=font(30, 600), fill=(236, 152, 132), anchor='mm')
    im.save(ART / 'scene_02.png')
    print('scene_02.png')


def scene_03():
    im, d = base()
    heading(d, '開けている時間を半分に', y=400, note='1回20秒 → 10秒')
    for i, (label, sec, col) in enumerate([('20秒', 20, (150, 120, 110)), ('10秒', 10, BLUE)]):
        y = 620 + i * 230
        d.text((140, y + 60), label, font=font(44, 800), fill=col, anchor='lm')
        d.rounded_rectangle((280, y, 980, y + 120), 20, fill=(26, 38, 50), outline=(70, 86, 100), width=3)
        d.rounded_rectangle((280, y, 280 + 700 * sec / 20, y + 120), 20, fill=col + (210,))
    money(d, '年 約740円', 1180)
    im.save(ART / 'scene_03.png')
    print('scene_03.png')


def scene_04():
    im, d = base()
    heading(d, '開閉の回数を半分に', y=400, note='冷蔵室30回 → 15回（1日）')
    for i, (label, n, col) in enumerate([('30回', 30, (150, 120, 110)), ('15回', 15, BLUE)]):
        y = 640 + i * 220
        d.text((150, y + 55), label, font=font(42, 800), fill=col, anchor='lm')
        for k in range(n if n <= 30 else 30):
            x = 300 + (k % 15) * 46
            yy = y + (k // 15) * 60
            d.rounded_rectangle((x, yy, x + 36, yy + 46), 8, fill=col + (220,))
    money(d, '年 約340円', 1180)
    im.save(ART / 'scene_04.png')
    print('scene_04.png')


def scene_05():
    im, d = base()
    heading(d, '壁から離して置く', y=380, note='上と両側が壁 vs 片側が壁')
    # 上面図
    cx, cy = 400, 760
    d.rounded_rectangle((cx - 220, cy - 160, cx + 220, cy + 160), 16, outline=(120, 134, 148), width=6)
    d.text((cx, cy), '冷蔵庫', font=font(34, 700), fill=WHITE, anchor='mm')
    for (x0, y0, x1, y1) in [(cx - 260, cy - 200, cx + 260, cy - 170), (cx - 260, cy + 170, cx + 260, cy + 200),
                             (cx - 260, cy - 200, cx - 230, cy + 200), (cx + 230, cy - 200, cx + 260, cy + 200)]:
        d.rectangle((x0, y0, x1, y1), fill=(90, 104, 118))
    d.text((cx, cy + 250), '壁に囲まれていると熱がこもる', font=font(26, 600), fill=DIM, anchor='mm')

    # 合計バー
    bars = [('設定', 1970, GOLD), ('開放時間', 740, BLUE), ('開閉回数', 340, (150, 200, 160)), ('設置', 1400, (200, 160, 210))]
    base_y, scale = 1330, 300 / 1970
    x = 120
    for label, v, col in bars:
        h = max(20, v * scale)
        d.rounded_rectangle((x, base_y - h, x + 150, base_y), 10, fill=col + (220,))
        d.text((x + 75, base_y + 34), label, font=font(20, 600), fill=DIM, anchor='mm')
        x += 200
    d.text((W // 2, 1450), '合計 年 約4,450円', font=font(66, 800), fill=GOLD, anchor='mm')
    d.text((W // 2, 1530), '※ 単純な足し算。実際は効果が重なる', font=font(22, 500), fill=DIM, anchor='mm')
    im.save(ART / 'scene_05.png')
    print('scene_05.png')


def scene_06():
    im, d = base()
    heading(d, '設定を下げるときの注意', y=420)
    items = ['温度を下げると食品が傷みやすい', '公的資料も「傷みに注意」と付記', '夏場は特に注意する', '熱いものはさましてから入れる']
    y = 580
    for it in items:
        d.rounded_rectangle((80, y, W - 80, y + 130), 18, fill=(24, 36, 48, 235), outline=(60, 76, 92), width=2)
        d.text((120, y + 65), '・' + it, font=font(32, 600), fill=WHITE, anchor='lm')
        y += 150
    d.text((W // 2, y + 40), '節約より、食品を守るほうが優先', font=font(30, 700), fill=GOLD, anchor='mm')
    im.save(ART / 'scene_06.png')
    print('scene_06.png')


if __name__ == '__main__':
    for fn in (scene_01, scene_02, scene_03, scene_04, scene_05, scene_06):
        fn()
