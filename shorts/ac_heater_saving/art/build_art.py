"""ac_heater_saving の図解素材（シーン2〜5）を作る。

数値と文字はここで正確に描く（生成AIに任せない）。写真が要るシーン1・6は生成AIのイメージ。
  python shorts/ac_heater_saving/art/build_art.py
出力: shorts/ac_heater_saving/art/scene_02.png … scene_05.png（1080x1920）
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
FAINT = (58, 70, 82)
BLUE = (128, 186, 236)
GREEN = (126, 206, 160)

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


def heading(d, text, y=420, size=44, note=None):
    d.text((W // 2, y), text, font=font(size, 700), fill=WHITE, anchor='mm')
    d.line([(W // 2 - 230, y + 48), (W // 2 + 230, y + 48)], fill=GOLD + (200,), width=3)
    if note:
        d.text((W // 2, y + 96), note, font=font(26, 500), fill=DIM, anchor='mm')


ROWS = [
    ('設定温度を1℃下げる', 490, '約490円', GOLD),
    ('1日1時間だけ短くする', 1110, '約1,110円', BLUE),
    ('フィルターを掃除する', 1170, '約1,170円', GREEN),
]
X0, MAXW, MAXV = 380, 430, 1200.0
YS = [640, 830, 1020]


def bars(n):
    """n 本ぶんを実線で描き、残りは「まだ出していない」薄い枠で置いておく（同じ構図で1本ずつ増やす）。"""
    im, d = base()
    heading(d, '年間の節約額', y=430, note='資源エネルギー庁の試算（2.5kWの機器・東京の木造住宅）')
    for i, (label, val, txt, col) in enumerate(ROWS):
        y = YS[i]
        on = i < n
        d.text((X0 - 28, y + 48), label, font=font(30, 600),
               fill=(WHITE if on else (96, 106, 118)), anchor='rm')
        w = int(val / MAXV * MAXW)
        if on:
            d.rounded_rectangle((X0, y, X0 + w, y + 96), 12, fill=col + (235,))
            d.text((X0 + w + 22, y + 48), txt, font=font(38, 700), fill=col, anchor='lm')
        else:
            d.rounded_rectangle((X0, y, X0 + MAXW, y + 96), 12, outline=FAINT + (255,), width=3)
            d.text((X0 + 26, y + 48), '？', font=font(40, 700), fill=(78, 90, 102), anchor='lm')
    d.text((W // 2, 1210), '同じ資料・同じ条件での試算', font=font(26, 500), fill=DIM, anchor='mm')
    return im


def scene_05():
    """試算の条件。数字の前提を画面に出す（説明欄にも同じ内容を書く）。"""
    im, d = base()
    heading(d, 'この金額の条件', y=430)
    items = [
        ('住宅', '東京をモデルとした\n木造南向き住宅'),
        ('機器', 'エアコン 2.5kW'),
        ('電気料金', '31円/kWh で換算'),
    ]
    y = 560
    for name, val in items:
        d.rounded_rectangle((70, y, W - 70, y + 168), 20, fill=(24, 36, 48, 235), outline=(60, 76, 92), width=2)
        d.text((110, y + 38), name, font=font(27, 600), fill=DIM, anchor='lm')
        d.multiline_text((110, y + 72), val, font=font(33, 700), fill=WHITE, spacing=6)
        y += 190
    d.text((W // 2, y + 40), '地域・機器・使い方で変わります', font=font(30, 600), fill=GOLD, anchor='mm')
    d.text((W // 2, y + 92), '※ 31円/kWh は令和4年7月の新電力料金目安単価',
           font=font(24, 500), fill=DIM, anchor='mm')
    return im


def scene_07():
    """プロフィール欄に掃除用ブラシの商品ページを置いている、という案内。"""
    im, d = base()
    heading(d, '道具の置き場所', y=430)

    px, py, pw, ph = 300, 490, 480, 560
    d.rounded_rectangle((px, py, px + pw, py + ph), 44, fill=(16, 24, 32), outline=(70, 86, 100), width=6)
    d.rounded_rectangle((px + 18, py + 18, px + pw - 18, py + ph - 18), 30, fill=(24, 34, 45))
    d.ellipse((px + 48, py + 56, px + 128, py + 136), fill=(58, 74, 90))
    d.text((px + 148, py + 96), 'チャンネル', font=font(30, 600), fill=WHITE, anchor='lm')
    d.line([(px + 40, py + 172), (px + pw - 40, py + 172)], fill=(60, 76, 92), width=2)
    d.text((px + 48, py + 226), 'プロフィール', font=font(26, 600), fill=DIM, anchor='lm')
    d.rounded_rectangle((px + 40, py + 262, px + pw - 40, py + 372), 18, fill=(32, 46, 60))
    ix, iy = px + 72, py + 300
    d.rounded_rectangle((ix - 20, iy - 20, ix + 20, iy + 20), 10, outline=GOLD, width=3)
    d.text((ix, iy - 2), '↗', font=font(28, 700), fill=GOLD, anchor='mm')
    d.text((px + 118, py + 300), '掃除用ブラシ', font=font(32, 700), fill=WHITE, anchor='lm')
    d.text((px + 66, py + 344), '商品ページ', font=font(24, 500), fill=DIM, anchor='lm')
    d.text((px + 48, py + 430), '説明欄のURLは', font=font(24, 500), fill=(140, 152, 164), anchor='lm')
    d.text((px + 48, py + 466), 'タップできないため', font=font(24, 500), fill=(140, 152, 164), anchor='lm')

    d.line([(W // 2, py + ph + 24), (W // 2, py + ph + 86)], fill=GOLD, width=8)
    d.polygon([(W // 2, py + ph + 122), (W // 2 - 26, py + ph + 76), (W // 2 + 26, py + ph + 76)], fill=GOLD)
    d.text((W // 2, py + ph + 150), 'プロフィールのリンクへ', font=font(36, 700), fill=GOLD, anchor='mm')
    return im


if __name__ == '__main__':
    for i, n in ((2, 1), (3, 2), (4, 3)):
        bars(n).save(ART / ('scene_%02d.png' % i))
        print('scene_%02d.png' % i)
    scene_05().save(ART / 'scene_05.png')
    print('scene_05.png')




