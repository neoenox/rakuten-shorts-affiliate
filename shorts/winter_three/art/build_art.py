"""winter_three の素材（6枚）を作る。シーン1は自作イラスト、2〜6は模式図。"""
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


def heading(d, text, y=400, size=42, note=None):
    d.text((W // 2, y), text, font=font(size, 700), fill=WHITE, anchor='mm')
    d.line([(W // 2 - 250, y + 46), (W // 2 + 250, y + 46)], fill=GOLD + (200,), width=3)
    if note:
        d.text((W // 2, y + 94), note, font=font(25, 500), fill=DIM, anchor='mm')


def money(d, text, y, color=GOLD, size=84):
    d.text((W // 2, y), text, font=font(size, 800), fill=color, anchor='mm')


def scene_01():
    im, d = base()
    # 壁と窓
    d.rectangle((0, 0, W, 1250), fill=(24, 32, 44))
    d.rounded_rectangle((620, 420, 1000, 900), 16, fill=(30, 58, 86), outline=(60, 90, 120), width=6)
    # エアコン
    d.rounded_rectangle((90, 300, 520, 420), 22, fill=(232, 234, 238), outline=(200, 204, 210), width=4)
    d.rectangle((90, 400, 520, 424), fill=(206, 210, 216))
    for i in range(9):
        d.line([(120 + i * 44, 430), (140 + i * 44, 520)], fill=(150, 180, 210, 120), width=6)
    # 床とこたつ
    d.rectangle((0, 1250, W, H), fill=(38, 32, 30))
    d.rounded_rectangle((220, 1300, 860, 1560), 28, fill=(96, 74, 62))
    d.rounded_rectangle((260, 1330, 820, 1520), 20, fill=(120, 92, 76))
    # 人物（後ろ姿）
    d.ellipse((470, 1180, 610, 1320), fill=(58, 54, 66))
    d.rounded_rectangle((430, 1300, 650, 1480), 60, fill=(70, 66, 80))
    d.text((W // 2, 1660), '冬のリビング', font=font(30, 600), fill=DIM, anchor='mm')
    im.save(ART / 'scene_01.png')
    print('scene_01.png')


def scene_02():
    im, d = base()
    heading(d, '設定温度を1℃下げる', y=400, note='東京・木造南向き・2.5kWの試算')
    # リモコン
    d.rounded_rectangle((330, 640, 750, 1180), 40, fill=(28, 36, 46), outline=(90, 104, 118), width=6)
    d.rounded_rectangle((370, 700, 710, 900), 20, fill=(18, 60, 54))
    d.text((540, 760), '暖房', font=font(30, 600), fill=(140, 200, 180), anchor='mm')
    d.text((540, 850), '21℃ → 20℃', font=font(52, 800), fill=WHITE, anchor='mm')
    d.text((540, 1030), '−1℃', font=font(64, 800), fill=GOLD, anchor='mm')
    money(d, '年 約490円', 1330)
    im.save(ART / 'scene_02.png')
    print('scene_02.png')


def scene_03():
    im, d = base()
    heading(d, '1日1時間 短くする', y=400, note='同じ条件での試算')
    # 24時間の帯
    x0, x1, y = 100, 980, 760
    d.rounded_rectangle((x0, y, x1, y + 120), 18, fill=(30, 46, 60), outline=(70, 86, 100), width=3)
    for i in range(1, 24):
        x = x0 + (x1 - x0) * i / 24
        d.line([(x, y), (x, y + 120)], fill=(60, 76, 92), width=2)
    # 削る1時間
    cut0 = x0 + (x1 - x0) * 23 / 24
    d.rectangle((cut0, y, x1, y + 120), fill=(236, 132, 112, 220))
    d.text((W // 2, y + 170), '24時間のうち1時間を削る', font=font(28, 600), fill=DIM, anchor='mm')
    money(d, '年 約1,110円', 1180)
    d.text((W // 2, 1300), '1時間 × 365日', font=font(28, 500), fill=DIM, anchor='mm')
    im.save(ART / 'scene_03.png')
    print('scene_03.png')


def scene_04():
    im, d = base()
    heading(d, 'フィルターを2週に1回', y=400, note='目詰まりが取れると風が通る')
    for i, (label, alpha, col) in enumerate([('before', 230, (150, 120, 110)), ('after', 90, (128, 186, 236))]):
        cx = 300 + i * 480
        d.rounded_rectangle((cx - 170, 640, cx + 170, 980), 16, outline=(180, 190, 200), width=6)
        for gx in range(cx - 150, cx + 160, 24):
            d.line([(gx, 650), (gx, 970)], fill=col + (alpha,), width=8)
        d.text((cx, 1040), label, font=font(30, 600), fill=DIM, anchor='mm')
    d.text((W // 2, 1130), '目詰まり → 通風が戻る', font=font(30, 600), fill=WHITE, anchor='mm')
    money(d, '年 約1,170円', 1300)
    im.save(ART / 'scene_04.png')
    print('scene_04.png')


def scene_05():
    im, d = base()
    heading(d, '3つの合計', y=400, note='単純な足し算。実際は効果が重なる')
    bars = [('1℃下げる', 490, GOLD), ('1時間短縮', 1110, BLUE), ('フィルター掃除', 1170, (150, 200, 160))]
    base_y = 1150
    scale = 520 / 1170
    x = 150
    for label, v, col in bars:
        h = max(28, v * scale)
        d.rounded_rectangle((x, base_y - h, x + 170, base_y), 12, fill=col + (225,))
        d.text((x + 85, base_y - h - 34), f'{v:,}', font=font(30, 800), fill=col, anchor='mm')
        d.text((x + 85, base_y + 44), label, font=font(22, 600), fill=DIM, anchor='mm')
        x += 230
    money(d, '年 約2,770円', 1360)
    im.save(ART / 'scene_05.png')
    print('scene_05.png')


def scene_06():
    im, d = base()
    heading(d, 'この金額の条件', y=400)
    items = [('住宅', '東京をモデルとした木造南向き'), ('機器', 'エアコン 2.5kW'), ('単価', '31円/kWh で換算')]
    y = 540
    for name, val in items:
        d.rounded_rectangle((70, y, W - 70, y + 160), 20, fill=(24, 36, 48, 235), outline=(60, 76, 92), width=2)
        d.text((110, y + 36), name, font=font(26, 600), fill=DIM, anchor='lm')
        d.text((110, y + 96), val, font=font(34, 700), fill=WHITE, anchor='lm')
        y += 182
    d.text((W // 2, y + 30), '地域・住宅・機器で変わります', font=font(30, 600), fill=GOLD, anchor='mm')
    d.text((W // 2, y + 82), '※ 31円/kWh は令和4年7月の新電力料金目安単価', font=font(22, 500), fill=DIM, anchor='mm')
    im.save(ART / 'scene_06.png')
    print('scene_06.png')


if __name__ == '__main__':
    for fn in (scene_01, scene_02, scene_03, scene_04, scene_05, scene_06):
        fn()
