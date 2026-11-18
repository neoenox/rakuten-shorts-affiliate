"""fridge_habits を7シーン構成に直し、図解を3枚に分ける。"""
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


def scene_05():
    im, d = base()
    heading(d, '設置の差で およそ1,400円', y=380, size=36, note='上と両側が壁 vs 片側だけ壁')

    def plan(cx, cy, walls, label, col):
        d.rounded_rectangle((cx - 150, cy - 110, cx + 150, cy + 110), 14, outline=(130, 144, 158), width=5)
        d.text((cx, cy), '冷蔵庫', font=font(28, 700), fill=WHITE, anchor='mm')
        if 'top' in walls:
            d.rectangle((cx - 175, cy - 140, cx + 175, cy - 118), fill=(98, 112, 126))
        if 'left' in walls:
            d.rectangle((cx - 178, cy - 140, cx - 154, cy + 140), fill=(98, 112, 126))
        if 'right' in walls:
            d.rectangle((cx + 154, cy - 140, cx + 178, cy + 140), fill=(98, 112, 126))
        d.text((cx, cy + 170), label, font=font(26, 700), fill=col, anchor='mm')

    plan(300, 700, ['top', 'left', 'right'], '上と両側が壁', WARM)
    plan(790, 700, ['top', 'left'], '片側だけ壁', BLUE)
    d.text((W // 2, 1010), 'この2条件の差が およそ1,400円', font=font(30, 600), fill=WHITE, anchor='mm')
    d.text((W // 2, 1150), '一年でおよそ1,400円', font=font(74, 800), fill=GOLD, anchor='mm')
    im.save(ART / 'scene_05.png')
    print('scene_05.png')


def scene_06():
    im, d = base()
    heading(d, '4つの合計', y=420, size=44, note='単純な足し算。合計は目安')
    bars = [('設定', 1970, GOLD), ('時間', 740, BLUE), ('回数', 340, (150, 200, 160)), ('設置', 1400, (200, 160, 210))]
    base_y, scale = 1100, 420 / 1970
    x = 120
    for label, v, col in bars:
        h = max(24, v * scale)
        d.rounded_rectangle((x, base_y - h, x + 170, base_y), 12, fill=col + (225,))
        d.text((x + 85, base_y - h - 34), f'{v:,}', font=font(28, 800), fill=col, anchor='mm')
        d.text((x + 85, base_y + 42), label, font=font(22, 600), fill=DIM, anchor='mm')
        x += 225
    d.text((W // 2, 1300), '合計 およそ4,450円', font=font(70, 800), fill=GOLD, anchor='mm')
    d.text((W // 2, 1390), '※ 4つ同時に実行した額の実測ではない', font=font(24, 500), fill=DIM, anchor='mm')
    im.save(ART / 'scene_06.png')
    print('scene_06.png')


def scene_07():
    im, d = base()
    heading(d, '弱にすると、庫内温度は上がる', y=400, size=34)
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
    im.save(ART / 'scene_07.png')
    print('scene_07.png')


def rebuild_script():
    p = Path('shorts/fridge_habits/result.json')
    d = json.loads(p.read_text(encoding='utf-8'))
    old = d['scenes']
    art = [old[0], old[1], old[2], old[3]]

    s5 = {
        'start': 0, 'end': 0,
        'narration': '壁に囲まれた設置と片側だけ空いた設置では、一年でおよそ1400円の差です。',
        'caption': ['設置の差で', '一年でおよそ1,400円'],
        'visual': '模式図。上と両側が壁の設置と、片側だけ壁の設置の上面図を並べ、金額を示す。',
        'claim_ids': ['c4'],
    }
    s6 = {
        'start': 0, 'end': 0,
        'narration': '4つの合計は、およそ4450円です。',
        'caption': ['4つの合計', 'およそ4,450円'],
        'visual': '模式図。4本のバー（1,970・740・340・1,400）を並べ、合計4,450円を示す。「単純な足し算で、合計は目安」と注記。',
        'claim_ids': ['c1', 'c2', 'c3', 'c4'],
    }
    s7 = {
        'start': 0, 'end': 0,
        'narration': '設定を弱めると、庫内の温度は上がります。食品の傷みに注意してください。',
        'caption': ['弱にすると庫内温度は上がる', '食品の傷みに注意'],
        'visual': '模式図。注意のパネル。「庫内の温度が上がる」「食品が傷みやすい」「夏場は特に注意」を箇条書きで示す。',
        'claim_ids': ['c5'],
    }
    d['scenes'] = art + [s5, s6, s7]
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('scenes:', len(d['scenes']))


if __name__ == '__main__':
    scene_05()
    scene_06()
    scene_07()
    rebuild_script()
