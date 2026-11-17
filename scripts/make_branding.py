"""チャンネルのプロフィール画像とバナーを作る（PIL）。

  python scripts/make_branding.py
出力: assets/branding/profile.png（800x800）, assets/branding/banner.png（2048x1152）
バナーの安全領域は 1546x423（中央）。文字はその中に収める。
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets' / 'branding'
FONT = 'C:/Windows/Fonts/NotoSansJP-VF.ttf'
BG = (11, 17, 24)
BG2 = (20, 30, 40)
GOLD = (239, 201, 118)
WHITE = (246, 244, 236)
DIM = (150, 162, 174)


def font(size, weight=700):
    f = ImageFont.truetype(FONT, size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def gradient(w, h):
    im = Image.new('RGB', (w, h), BG)
    d = ImageDraw.Draw(im)
    for y in range(h):
        r = y / max(1, h - 1)
        d.line([(0, y), (w, y)], fill=tuple(round(BG[i] + (BG2[i] - BG[i]) * r) for i in range(3)))
    return im


def profile():
    size = 800
    im = gradient(size, size)
    d = ImageDraw.Draw(im, 'RGBA')
    d.rounded_rectangle((36, 36, size - 36, size - 36), 150, outline=GOLD + (230,), width=14)
    d.text((size / 2, size / 2 + 12), '判', font=font(430, 800), fill=GOLD, anchor='mm')
    im.save(OUT / 'profile.png')
    print('profile.png')


def banner():
    w, h = 2048, 1152
    im = gradient(w, h)
    d = ImageDraw.Draw(im, 'RGBA')
    # 安全領域（1546x423）の中心に文字を置く
    cy = h // 2
    d.text((w / 2, cy - 70), '暮らしの判断メモ', font=font(132, 800), fill=WHITE, anchor='mm')
    d.line([(w / 2 - 320, cy + 22), (w / 2 + 320, cy + 22)], fill=GOLD + (230,), width=6)
    d.text((w / 2, cy + 110), '数字で、暮らしの判断を。', font=font(64, 600), fill=GOLD, anchor='mm')
    d.text((w / 2, cy + 200), '電気代・暖房・キッチン　出典つきで30〜45秒', font=font(44, 500), fill=DIM, anchor='mm')
    im.save(OUT / 'banner.png')
    print('banner.png')


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    profile()
    banner()


