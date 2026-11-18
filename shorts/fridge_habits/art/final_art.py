"""fridge_habits の図解（シーン2〜7）を、字幕帯（y=1252〜）に重ならない配置で描く。"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
SAFE_BOTTOM = 1215          # これより下は字幕帯
ART = Path('shorts/fridge_habits/art')
FONT = 'C:/Windows/Fonts/NotoSansJP-VF.ttf'
BG_TOP, BG_BOT = (10, 16, 24), (20, 30, 40)
GOLD = (239, 201, 118)
WHITE = (246, 244, 236)
DIM = (150, 162, 174)
BLUE = (128, 186, 236)
WARM = (226, 150, 120)

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


def heading(d, text, y=360, size=40, note=None):
    d.text((W // 2, y), text, font=font(size, 700), fill=WHITE, anchor='mm')
    d.line([(W // 2 - 250, y + 46), (W // 2 + 250, y + 46)], fill=GOLD + (200,), width=3)
    if note:
        d.text((W // 2, y + 92), note, font=font(24, 500), fill=DIM, anchor='mm')


def scene_02():
    im, d = base()
    heading(d, '設定を「中」から「弱」へ', y=380, note='年間の差（公的資料の試算）')
    cx, cy, r = 540, 690, 130
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(90, 104, 118), width=10)
    d.text((cx - 55, cy - 34), '中', font=font(52, 700), fill=DIM, anchor='mm')
    d.line([(cx, cy + 16), (cx + 66, cy + 62)], fill=GOLD, width=11)
    d.text((cx + 26, cy + 84), '弱', font=font(44, 700), fill=GOLD, anchor='mm')
    d.text((W // 2, 930), '一年でおよそ1,970円', font=font(74, 800), fill=GOLD, anchor='mm')
    d.text((W // 2, 1040), '※ 弱にすると庫内の温度は上がる', font=font(28, 600), fill=WARM, anchor='mm')
    d.text((W // 2, 1100), '食品の傷みに注意', font=font(28, 600), fill=WARM, anchor='mm')
    im.save(ART / 'scene_02.png')
    print('scene_02.png')


def scene_03():
    im, d = base()
    heading(d, '開けている時間を半分に', y=380, note='1回20秒 → 10秒')
    for i, (label, sec, col) in enumerate([('20秒', 20, (150, 120, 110)), ('10秒', 10, BLUE)]):
        y = 580 + i * 200
        d.text((130, y + 55), label, font=font(42, 800), fill=col, anchor='lm')
        d.rounded_rectangle((270, y, 970, y + 110), 18, fill=(26, 38, 50), outline=(70, 86, 100), width=3)
        d.rounded_rectangle((270, y, 270 + 690 * sec / 20, y + 110), 18, fill=col + (210,))
    d.text((W // 2, 1030), '一年でおよそ740円', font=font(74, 800), fill=GOLD, anchor='mm')
    d.text((W // 2, 1110), '1時間 × 365日', font=font(28, 500), fill=DIM, anchor='mm')
    im.save(ART / 'scene_03.png')
    print('scene_03.png')


def scene_04():
    im, d = base()
    heading(d, '開閉の回数を半分に', y=360, note='1回の開閉を10秒と想定')
    rows = [('冷蔵室', 30, 15), ('冷凍室', 8, 4)]
    y = 520
    for label, before, after in rows:
        d.text((110, y + 30), label, font=font(32, 700), fill=WHITE, anchor='lm')
        d.text((110, y + 96), f'{before}回 → {after}回', font=font(38, 800), fill=GOLD, anchor='lm')
        for k in range(before):
            x = 470 + (k % 15) * 38
            yy = y + (k // 15) * 48
            col = WARM if k < after else (150, 120, 110)
            d.rounded_rectangle((x, yy, x + 30, yy + 38), 7, fill=col + (215,))
        y += 290
    d.text((W // 2, 1010), '一年でおよそ340円', font=font(74, 800), fill=GOLD, anchor='mm')
    d.text((W // 2, 1090), '減らした分だけ電気が減る', font=font(26, 500), fill=DIM, anchor='mm')
    im.save(ART / 'scene_04.png')
    print('scene_04.png')


def scene_05():
    im, d = base()
    heading(d, '設置の差で およそ1,400円', y=360, size=36, note='上と両側が壁 vs 片側だけ壁')

    def plan(cx, cy, walls, label, col):
        d.rounded_rectangle((cx - 140, cy - 100, cx + 140, cy + 100), 14, outline=(130, 144, 158), width=5)
        d.text((cx, cy), '冷蔵庫', font=font(26, 700), fill=WHITE, anchor='mm')
        if 'top' in walls:
            d.rectangle((cx - 165, cy - 128, cx + 165, cy - 108), fill=(98, 112, 126))
        if 'left' in walls:
            d.rectangle((cx - 168, cy - 128, cx - 146, cy + 128), fill=(98, 112, 126))
        if 'right' in walls:
            d.rectangle((cx + 146, cy - 128, cx + 168, cy + 128), fill=(98, 112, 126))
        d.text((cx, cy + 156), label, font=font(25, 700), fill=col, anchor='mm')

    plan(300, 650, ['top', 'left', 'right'], '上と両側が壁', WARM)
    plan(790, 650, ['top', 'left'], '片側だけ壁', BLUE)
    d.text((W // 2, 960), 'この2条件の差が およそ1,400円', font=font(28, 600), fill=WHITE, anchor='mm')
    d.text((W // 2, 1060), '一年でおよそ1,400円', font=font(70, 800), fill=GOLD, anchor='mm')
    im.save(ART / 'scene_05.png')
    print('scene_05.png')


def scene_06():
    im, d = base()
    heading(d, '4つの合計', y=400, size=44, note='単純な足し算。合計は目安')
    bars = [('設定', 1970, GOLD), ('時間', 740, BLUE), ('回数', 340, (150, 200, 160)), ('設置', 1400, (200, 160, 210))]
    base_y, scale = 1010, 380 / 1970
    x = 120
    for label, v, col in bars:
        h = max(22, v * scale)
        d.rounded_rectangle((x, base_y - h, x + 170, base_y), 12, fill=col + (225,))
        d.text((x + 85, base_y - h - 30), f'{v:,}', font=font(26, 800), fill=col, anchor='mm')
        d.text((x + 85, base_y + 38), label, font=font(21, 600), fill=DIM, anchor='mm')
        x += 225
    d.text((W // 2, 1100), '合計 およそ4,450円', font=font(64, 800), fill=GOLD, anchor='mm')
    d.text((W // 2, 1175), '※ 4つ同時の実測ではない', font=font(23, 500), fill=DIM, anchor='mm')
    im.save(ART / 'scene_06.png')
    print('scene_06.png')


def scene_07():
    im, d = base()
    heading(d, '弱にすると、庫内温度は上がる', y=380, size=34)
    items = [
        ('庫内の温度が上がる', '冷えにくくなる'),
        ('食品が傷みやすくなる', '公的資料も注意を促す'),
        ('夏場は特に注意', '設定は自己責任で'),
        ('熱いものはさましてから', '庫内温度を上げない'),
    ]
    y = 520
    for head, sub in items:
        d.rounded_rectangle((80, y, W - 80, y + 140), 18, fill=(24, 36, 48, 235), outline=(60, 76, 92), width=2)
        d.text((120, y + 48), '・' + head, font=font(30, 700), fill=WHITE, anchor='lm')
        d.text((120, y + 100), '　' + sub, font=font(23, 500), fill=DIM, anchor='lm')
        y += 156
    d.text((W // 2, y + 20), '節約より、食品を守るほうが優先', font=font(26, 700), fill=GOLD, anchor='mm')
    im.save(ART / 'scene_07.png')
    print('scene_07.png')


if __name__ == '__main__':
    scene_02(); scene_03(); scene_04(); scene_05(); scene_06(); scene_07()
    print('safe bottom:', SAFE_BOTTOM)
