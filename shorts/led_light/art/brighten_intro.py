"""led_light の冒頭イラストを明るく描き直す（暗すぎて空に見えるため）。"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
ART = Path('shorts/led_light/art')
FONT = 'C:/Windows/Fonts/NotoSansJP-VF.ttf'
WHITE = (246, 244, 236)
DIM = (170, 180, 192)
GOLD = (239, 201, 118)


def font(size, weight=600):
    f = ImageFont.truetype(FONT, size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def main():
    im = Image.new('RGB', (W, H), (18, 20, 26))
    d = ImageDraw.Draw(im, 'RGBA')

    # 壁と床（明るめの寒色）
    d.rectangle((0, 0, W, 1300), fill=(34, 40, 52))
    d.rectangle((0, 1300, W, H), fill=(66, 52, 42))

    # 天井の照明（ワイヤ＋笠）
    d.line([(540, 0), (540, 130)], fill=(140, 132, 120), width=10)
    d.polygon([(400, 130), (680, 130), (620, 250), (460, 250)], fill=(248, 226, 168))
    d.ellipse((470, 240, 610, 280), fill=(255, 246, 210))

    # 光の広がり（明るく・大きく）
    for r in range(760, 0, -40):
        alpha = max(0, int(26 - r / 40))
        d.ellipse((540 - r, 300 - r * 0.55, 540 + r, 300 + r * 0.55), fill=(255, 228, 170, alpha))

    # 光の帯（床へ落ちる）
    d.polygon([(470, 300), (610, 300), (860, 1300), (220, 1300)], fill=(255, 230, 175, 22))

    # 机
    d.rectangle((80, 1120, 620, 1180), fill=(150, 112, 84))
    d.rectangle((120, 1180, 170, 1320), fill=(126, 94, 70))
    d.rectangle((530, 1180, 580, 1320), fill=(126, 94, 70))

    # 人物（後ろ姿）
    d.ellipse((600, 880, 780, 1060), fill=(74, 70, 88))
    d.rounded_rectangle((560, 1040, 820, 1300), 70, fill=(88, 84, 104))

    # 机の上のノート（白い面で明るさを出す）
    d.rounded_rectangle((170, 1060, 470, 1120), 8, fill=(236, 234, 226))
    d.line([(200, 1085), (440, 1085)], fill=(180, 178, 170), width=3)
    d.line([(200, 1105), (400, 1105)], fill=(180, 178, 170), width=3)

    im.save(ART / 'scene_01.png')
    print('scene_01.png を明るく描き直した')


if __name__ == '__main__':
    main()
