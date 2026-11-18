"""kettle_heat の素材6枚（1は自作イラスト、2〜6は模式図）。字幕帯 y=1252 より上に収める。"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
ART = Path('shorts/kettle_heat/art')
FONT = 'C:/Windows/Fonts/NotoSansJP-VF.ttf'
BG_TOP, BG_BOT = (10, 16, 24), (20, 30, 40)
GOLD = (239, 201, 118)
WHITE = (246, 244, 236)
DIM = (150, 162, 174)
BLUE = (128, 186, 236)
WARM = (236, 196, 130)
RED = (236, 132, 112)
GREEN = (150, 200, 160)

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


def scene_01():
    im, d = base()
    d.rectangle((0, 0, W, 1250), fill=(26, 30, 38))
    d.rectangle((0, 1250, W, H), fill=(56, 44, 38))
    # ポット
    d.rounded_rectangle((330, 640, 700, 1180), 40, fill=(226, 230, 236), outline=(198, 204, 212), width=6)
    d.rounded_rectangle((380, 700, 650, 780), 18, fill=(60, 90, 120))
    d.rounded_rectangle((330, 1120, 700, 1180), 20, fill=(180, 188, 198))
    d.line([(700, 760), (800, 760)], fill=(180, 188, 198), width=16)
    # 湯気
    for i in range(3):
        x = 420 + i * 90
        d.line([(x, 640), (x + 20, 560), (x, 480)], fill=(220, 230, 240, 120), width=8, joint='curve')
    # マグ
    d.rounded_rectangle((820, 980, 980, 1150), 22, fill=(210, 180, 150))
    d.line([(820, 1030), (790, 1030), (790, 1110), (820, 1110)], fill=(210, 180, 150), width=14)
    d.text((W // 2, 1560), '朝のキッチン', font=font(30, 600), fill=DIM, anchor='mm')
    im.save(ART / 'scene_01.png')
    print('scene_01.png')


def scene_02():
    im, d = base()
    heading(d, '保温をやめてプラグを抜く', y=360, size=34, note='6時間保温した場合との比較')
    # タイムライン
    x0, x1 = 110, 970
    y = 600
    d.text((110, y - 50), '6時間の保温', font=font(26, 600), fill=DIM, anchor='lm')
    d.rounded_rectangle((x0, y, x1, y + 90), 16, fill=(236, 132, 112, 200))
    d.text(((x0 + x1) // 2, y + 45), '保温をつづける', font=font(28, 700), fill=(40, 30, 30), anchor='mm')
    y2 = y + 170
    d.text((110, y2 - 50), 'プラグを抜く', font=font(26, 600), fill=DIM, anchor='lm')
    d.rounded_rectangle((x0, y2, x1, y2 + 90), 16, fill=(150, 200, 160, 200))
    d.text(((x0 + x1) // 2, y2 + 45), '使うときに沸かし直す', font=font(28, 700), fill=(30, 40, 30), anchor='mm')
    d.text((W // 2, 1060), '年 約3,330円', font=font(78, 800), fill=GOLD, anchor='mm')
    im.save(ART / 'scene_02.png')
    print('scene_02.png')


def scene_03():
    im, d = base()
    heading(d, 'この金額の条件', y=370)
    items = [('沸騰させる量', '2.2L 満タン'), ('使う量', '1.2L'), ('保温の時間', '6時間')]
    y = 540
    for name, val in items:
        d.rounded_rectangle((80, y, W - 80, y + 160), 20, fill=(24, 36, 48, 235), outline=(60, 76, 92), width=2)
        d.text((120, y + 36), name, font=font(25, 600), fill=DIM, anchor='lm')
        d.text((120, y + 98), val, font=font(38, 700), fill=WHITE, anchor='lm')
        y += 182
    d.text((W // 2, y + 20), 'この条件での試算です', font=font(26, 500), fill=GOLD, anchor='mm')
    im.save(ART / 'scene_03.png')
    print('scene_03.png')


def scene_04():
    im, d = base()
    heading(d, 'コンロは強火→中火', y=370, note='水1Lを沸騰・1日3回')
    # 鍋と炎（はみ出す／収まる）
    for i, (label, col, over) in enumerate([('強火（はみ出す）', RED, True), ('中火（底に収まる）', GREEN, False)]):
        cy = 640 + i * 300
        d.rounded_rectangle((320, cy, 760, cy + 70), 12, fill=(180, 188, 198))
        d.rectangle((360, cy + 70, 720, cy + 140), fill=(90, 100, 112))
        span = 300 if over else 320
        for k in range(5):
            x = 540 - span // 2 + k * (span // 4)
            h = 90 if over else 60
            d.polygon([(x, cy + 210), (x - 26, cy + 210 - h), (x + 26, cy + 210 - h)], fill=col + (220,))
        d.text((540, cy + 250), label, font=font(26, 700), fill=col, anchor='mm')
    d.text((W // 2, 1060), '年 約390円', font=font(74, 800), fill=GOLD, anchor='mm')
    im.save(ART / 'scene_04.png')
    print('scene_04.png')


def scene_05():
    im, d = base()
    heading(d, '2つの合計', y=400, size=44, note='単純な足し算。合計は目安')
    bars = [('ポット', 3330, GOLD), ('コンロ', 390, BLUE)]
    base_y, scale = 980, 340 / 3330
    for i, (lab, v, col) in enumerate(bars):
        h = max(24, v * scale)
        x = 320 + i * 420
        d.rounded_rectangle((x - 80, base_y - h, x + 80, base_y), 12, fill=col + (225,))
        d.text((x, base_y - h - 32), f'{v:,}', font=font(30, 800), fill=col, anchor='mm')
        d.text((x, base_y + 40), lab, font=font(24, 600), fill=DIM, anchor='mm')
    d.text((W // 2, 1080), '合計 年 約3,720円', font=font(66, 800), fill=GOLD, anchor='mm')
    d.text((W // 2, 1160), '※ 条件が違う2つを足した目安', font=font(23, 500), fill=DIM, anchor='mm')
    im.save(ART / 'scene_05.png')
    print('scene_05.png')


def scene_06():
    im, d = base()
    heading(d, '保温のしかた', y=380)
    items = [('低めの温度で保温', '使うときに沸かし直す'), ('長時間使わない', 'プラグを抜く'), ('買い替えるなら', '断熱を強化したタイプ')]
    y = 560
    for head, sub in items:
        d.rounded_rectangle((80, y, W - 80, y + 160), 20, fill=(24, 36, 48, 235), outline=(60, 76, 92), width=2)
        d.text((120, y + 50), '・' + head, font=font(32, 700), fill=WHITE, anchor='lm')
        d.text((120, y + 110), '　' + sub, font=font(24, 500), fill=DIM, anchor='lm')
        y += 180
    d.text((W // 2, y + 20), '手間と金額のどちらを取るかは人次第', font=font(24, 500), fill=GOLD, anchor='mm')
    im.save(ART / 'scene_06.png')
    print('scene_06.png')


if __name__ == '__main__':
    for fn in (scene_01, scene_02, scene_03, scene_04, scene_05, scene_06):
        fn()
