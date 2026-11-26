"""人物中心のストーリー動画で使う、共通キャラクターの描画ヘルパ（試作）。

実在の人物・商品・ロゴは描かない。色と形を固定することで、
シーンが変わっても「同じ人」だと分かる Like な記号だけを載せる。

使い方:
    from scripts.story_person import draw_person
    draw_person(draw, x=200, y=1100, s=1.0, pose='think')

    python scripts/story_person.py --demo   # 4ポーズの見本を docs/assets/ に出す
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONT = Path('C:/Windows/Fonts/NotoSansJP-VF.ttf')
SKIN = (238, 205, 176)
HAIR = (36, 40, 50)
TOP = (226, 170, 74)      # 固定: からし色のカーディガン
SHIRT = (238, 238, 230)
PANTS = (52, 70, 96)      # 固定: 濃い青のズボン
OUTLINE = (16, 22, 30)

POSES = ('notice', 'think', 'check', 'act', 'relieved')
LABELS = {'notice': '気づく', 'think': '考える', 'check': '確かめる',
          'act': '試す', 'relieved': '落ち着く'}


def font(size, weight=600):
    f = ImageFont.truetype(str(FONT), size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def draw_person(d, x, y, s=1.0, pose='think'):
    """(x, y) を足元の中心として、高さ 360*s px の人物を描く。"""
    if pose not in POSES:
        raise ValueError('pose must be one of %s' % (', '.join(POSES),))

    def P(px, py):
        return (int(round(x + px * s)), int(round(y + py * s)))

    def box(x1, y1, x2, y2, **kw):
        d.rounded_rectangle((P(x1, y1), P(x2, y2)), **kw)

    def line(points, fill, width):
        d.line([P(*p) for p in points], fill=fill, width=max(1, int(round(width * s))),
               joint='curve')

    # 脚・靴（形は全ポーズ共通）
    box(-50, -148, -12, -12, radius=int(12 * s), fill=PANTS)
    box(12, -148, 50, -12, radius=int(12 * s), fill=PANTS)
    box(-58, -20, -8, 0, radius=int(7 * s), fill=OUTLINE)
    box(8, -20, 58, 0, radius=int(7 * s), fill=OUTLINE)

    # 胴（からし色のカーディガン＋白いシャツ）
    box(-66, -252, 66, -132, radius=int(22 * s), fill=TOP, outline=OUTLINE,
        width=max(1, int(round(3 * s))))
    box(-14, -252, 14, -140, radius=int(6 * s), fill=SHIRT)

    # 腕（ポーズで手の位置だけ変える）
    hands = {
        'notice': ((-88, -158), (88, -158)),
        'think': ((-88, -160), (42, -280)),
        'check': ((-28, -188), (28, -188)),
        'act': ((-84, -162), (122, -226)),
        'relieved': ((-92, -172), (92, -172)),
    }
    (lx, ly), (rx, ry) = hands[pose]
    line([(-58, -236), (-90 if pose == 'think' else -78, -198), (lx, ly)], TOP, 26)
    line([(58, -236), (96 if pose in ('think', 'act') else 78, -198), (rx, ry)], TOP, 26)
    d.ellipse((P(lx - 13, ly - 13), P(lx + 13, ly + 13)), fill=SKIN)
    d.ellipse((P(rx - 13, ry - 13), P(rx + 13, ry + 13)), fill=SKIN)

    # 首・頭（髪型も固定。顔は記号だけ）
    box(-15, -268, 15, -238, radius=int(6 * s), fill=SKIN)
    d.ellipse((P(-53, -354), P(53, -248)), fill=SKIN, outline=OUTLINE,
              width=max(1, int(round(3 * s))))
    d.pieslice((P(-56, -360), P(56, -256)), 180, 360, fill=HAIR)
    d.ellipse((P(-56, -358), P(-30, -292)), fill=HAIR)
    d.ellipse((P(30, -358), P(56, -292)), fill=HAIR)

    d.ellipse((P(-22, -306), P(-14, -298)), fill=OUTLINE)
    d.ellipse((P(14, -306), P(22, -298)), fill=OUTLINE)
    if pose in ('notice', 'think', 'check'):
        d.line([P(-12, -278), P(12, -278)], fill=OUTLINE, width=max(1, int(round(3 * s))))
    else:
        d.arc((P(-18, -288), P(18, -266)), 10, 170, fill=OUTLINE,
              width=max(1, int(round(3 * s))))

    # 小道具は汎用のものだけ（実在商品は描かない）
    if pose == 'check':
        d.rounded_rectangle((P(-30, -202), P(30, -170)), radius=int(4 * s),
                            fill=(240, 240, 232), outline=OUTLINE,
                            width=max(1, int(round(2 * s))))
        d.line([P(-18, -186), P(18, -186)], fill=(120, 140, 160),
               width=max(1, int(round(2 * s))))


def demo(path=None):
    """4ポーズの接触シートを作る（ドキュメント用の見本）。"""
    dest = Path(path) if path else ROOT / 'docs' / 'assets' / 'story_person_sample.png'
    dest.parent.mkdir(parents=True, exist_ok=True)
    sheet = Image.new('RGB', (1080, 1920), (10, 16, 24))
    d = ImageDraw.Draw(sheet, 'RGBA')
    for i, pose in enumerate(('notice', 'think', 'check', 'relieved')):
        ox, oy = (i % 2) * 540, (i // 2) * 960
        for y in range(oy, oy + 960):
            r = (y - oy) / 960
            d.line([(ox, y), (ox + 540, y)],
                   fill=(int(12 + 10 * r), int(20 + 14 * r), int(30 + 16 * r), 255))
        # パネル用のローカル座標で描くため、一時画像に描いて貼る
        panel = Image.new('RGBA', (540, 960), (0, 0, 0, 0))
        pd = ImageDraw.Draw(panel, 'RGBA')
        draw_person(pd, 270, 880, s=0.9, pose=pose)
        sheet.paste(panel, (ox, oy), panel)
        d.text((ox + 270, oy + 110), LABELS[pose], font=font(44, 700),
               fill=(239, 201, 118, 255), anchor='mm')
        d.line([(ox + 20, oy + 958), (ox + 520, oy + 958)],
               fill=(60, 74, 88, 255), width=2)
    d.text((540, 960), '同じ人物・同じ色・同じ髪型', font=font(28, 500),
           fill=(150, 162, 174, 255), anchor='mm')
    sheet.save(dest)
    return dest


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description='人物中心ストーリーのキャラクター見本を出す')
    ap.add_argument('--demo', action='store_true', help='見本PNGを docs/assets に生成する')
    args = ap.parse_args()
    if args.demo:
        print(demo())
    else:
        ap.print_help()
