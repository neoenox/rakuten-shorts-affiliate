"""fridge_habits の冒頭イラストを描き直す（開いた扉と庫内が見える形に）。"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
ART = Path('shorts/fridge_habits/art')
FONT = 'C:/Windows/Fonts/NotoSansJP-VF.ttf'


def font(size, weight=600):
    f = ImageFont.truetype(FONT, size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def main():
    im = Image.new('RGB', (W, H), (26, 30, 38))
    d = ImageDraw.Draw(im, 'RGBA')

    # 壁・床
    d.rectangle((0, 0, W, 1240), fill=(38, 44, 56))
    d.rectangle((0, 1240, W, H), fill=(64, 52, 44))

    # 冷蔵庫の本体（庫内）
    body = (470, 360, 980, 1240)
    d.rounded_rectangle(body, 18, fill=(206, 216, 226), outline=(160, 172, 184), width=6)
    inner = (500, 400, 950, 1200)
    d.rounded_rectangle(inner, 12, fill=(246, 250, 252))

    # 棚と食品（色のブロックで表現）
    shelf_y = [560, 740, 920, 1080]
    for y in shelf_y:
        d.rectangle((510, y, 940, y + 14), fill=(190, 202, 214))
    items = [(530, 470, 640, 550, (226, 120, 110)), (660, 480, 760, 550, (150, 200, 160)),
             (780, 462, 900, 550, (240, 210, 150)), (540, 660, 660, 730, (170, 200, 235)),
             (690, 650, 820, 730, (200, 170, 210)), (540, 850, 700, 910, (240, 190, 140)),
             (730, 840, 880, 910, (160, 210, 190)), (540, 1000, 660, 1060, (230, 230, 226))]
    for x0, y0, x1, y1, col in items:
        d.rounded_rectangle((x0, y0, x1, y1), 10, fill=col + (235,))

    # 開いた扉（左側に立てる）
    d.polygon([(470, 360), (300, 300), (250, 1180), (470, 1240)], fill=(232, 238, 244))
    d.polygon([(470, 360), (300, 300), (250, 1180), (470, 1240)], outline=(180, 190, 200), width=4)
    # 扉の内側の棚ポケット
    for y in (520, 720, 920):
        d.polygon([(300, y), (440, y + 30), (440, y + 90), (300, y + 60)], outline=(190, 200, 212), width=3)

    # 庫内から漏れる光
    for r in range(360, 0, -30):
        d.ellipse((700 - r, 800 - r, 700 + r, 800 + r), fill=(220, 240, 255, 3))

    # 人物（後ろ姿）
    d.ellipse((70, 780, 250, 960), fill=(62, 60, 74))
    d.rounded_rectangle((30, 940, 290, 1240), 70, fill=(78, 74, 92))

    im.save(ART / 'scene_01.png')
    print('scene_01.png（開いた扉と庫内）')


if __name__ == '__main__':
    main()
