"""fridge_habits の図解を査読指摘に合わせて描き直す（シーン4・5・6）。"""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
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


def heading(d, text, y=400, size=40, note=None):
    d.text((W // 2, y), text, font=font(size, 700), fill=WHITE, anchor='mm')
    d.line([(W // 2 - 250, y + 46), (W // 2 + 250, y + 46)], fill=GOLD + (200,), width=3)
    if note:
        d.text((W // 2, y + 94), note, font=font(24, 500), fill=DIM, anchor='mm')


def scene_04():
    """冷蔵室と冷凍室の両方の回数を示す。"""
    im, d = base()
    heading(d, '開閉の回数を半分に', y=380, note='1回の開閉を10秒と想定')
    rows = [('冷蔵室', 30, 15), ('冷凍室', 8, 4)]
    y = 560
    for label, before, after in rows:
        d.text((110, y + 40), label, font=font(34, 700), fill=WHITE, anchor='lm')
        # before
        d.text((110, y + 110), f'{before}回 → {after}回', font=font(40, 800), fill=GOLD, anchor='lm')
        for k in range(before):
            x = 470 + (k % 15) * 38
            yy = y + (k // 15) * 48
            col = WARM if k < after else (150, 120, 110)
            d.rounded_rectangle((x, yy, x + 30, yy + 38), 7, fill=col + (215,))
        y += 320
    d.text((W // 2, 1120), '減らした分だけ電気が減る', font=font(28, 600), fill=DIM, anchor='mm')
    d.text((W // 2, 1250), '一年でおよそ340円', font=font(76, 800), fill=GOLD, anchor='mm')
    im.save(ART / 'scene_04.png')
    print('scene_04.png')


def scene_05():
    """設置の2条件を並べ、合計を示す。"""
    im, d = base()
    heading(d, '設置の差で およそ1,400円', y=370, size=36, note='上と両側が壁 vs 片側だけ壁')

    def plan(cx, cy, walls, label, col):
        d.rounded_rectangle((cx - 150, cy - 110, cx + 150, cy + 110), 14, outline=(130, 144, 158), width=5)
        d.text((cx, cy), '冷蔵庫', font=font(28, 700), fill=WHITE, anchor='mm')
        for side in walls:
            if side == 'top':
                d.rectangle((cx - 175, cy - 140, cx + 175, cy - 118), fill=(98, 112, 126))
            if side == 'left':
                d.rectangle((cx - 178, cy - 140, cx - 154, cy + 140), fill=(98, 112, 126))
            if side == 'right':
                d.rectangle((cx + 154, cy - 140, cx + 178, cy + 140), fill=(98, 112, 126))
        d.text((cx, cy + 170), label, font=font(26, 700), fill=col, anchor='mm')

    plan(300, 620, ['top', 'left', 'right'], '上と両側が壁', WARM)
    plan(790, 620, ['top', 'left'], '片側だけ壁', BLUE)

    d.text((W // 2, 900), 'この2条件の差が およそ1,400円', font=font(28, 600), fill=WHITE, anchor='mm')

    bars = [('設定', 1970, GOLD), ('時間', 740, BLUE), ('回数', 340, (150, 200, 160)), ('設置', 1400, (200, 160, 210))]
    base_y, scale = 1280, 240 / 1970
    x = 130
    for label, v, col in bars:
        h = max(18, v * scale)
        d.rounded_rectangle((x, base_y - h, x + 140, base_y), 10, fill=col + (220,))
        d.text((x + 70, base_y + 32), label, font=font(20, 600), fill=DIM, anchor='mm')
        x += 190
    d.text((W // 2, 1400), '合計 およそ4,450円', font=font(62, 800), fill=GOLD, anchor='mm')
    d.text((W // 2, 1480), '※ 単純な足し算。合計は目安', font=font(22, 500), fill=DIM, anchor='mm')
    im.save(ART / 'scene_05.png')
    print('scene_05.png')


def scene_06():
    """設定を弱めたときの注意（庫内温度は上がる）。"""
    im, d = base()
    heading(d, '弱にすると、庫内温度は上がる', y=400, size=36)
    items = [
        ('庫内の温度が上がる', '冷えにくくなる'),
        ('食品が傷みやすくなる', '公的資料も注意を促す'),
        ('夏場は特に注意', '設定は自己責任で'),
        ('熱いものはさましてから', '庫内温度を上げない'),
    ]
    y = 560
    for head, sub in items:
        d.rounded_rectangle((80, y, W - 80, y + 150), 18, fill=(24, 36, 48, 235), outline=(60, 76, 92), width=2)
        d.text((120, y + 52), '・' + head, font=font(32, 700), fill=WHITE, anchor='lm')
        d.text((120, y + 108), '　' + sub, font=font(24, 500), fill=DIM, anchor='lm')
        y += 168
    d.text((W // 2, y + 40), '節約より、食品を守るほうが優先', font=font(28, 700), fill=GOLD, anchor='mm')
    im.save(ART / 'scene_06.png')
    print('scene_06.png')


if __name__ == '__main__':
    scene_04()
    scene_05()
    scene_06()
