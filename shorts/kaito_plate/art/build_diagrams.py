"""kaito_plate の図解素材（scene_03 / 05 / 06）を作る。

写真は生成AIのイメージ、図解はここで描く（数値と文字を正確に出すため）。
  python shorts/kaito_plate/art/build_diagrams.py
出力: shorts/kaito_plate/art/scene_03.png, scene_05.png, scene_06.png（1080x1920）
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
ART = Path(__file__).resolve().parent
FONT = 'C:/Windows/Fonts/NotoSansJP-VF.ttf'
BG_TOP, BG_BOT = (10, 16, 24), (20, 30, 40)
GOLD = (239, 201, 118)
WHITE = (246, 244, 236)
DIM = (160, 172, 182)
BLUE = (128, 186, 236)
ORANGE = (240, 160, 110)

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
    for y in range(H):                       # 上下グラデーション
        r = y / H
        c = tuple(round(BG_TOP[i] + (BG_BOT[i] - BG_TOP[i]) * r) for i in range(3))
        d.line([(0, y), (W, y)], fill=c)
    for x in range(0, W, 60):                # 薄い方眼（図解らしさ）
        d.line([(x, 0), (x, H)], fill=(22, 34, 46), width=1)
    for y in range(0, H, 60):
        d.line([(0, y), (W, y)], fill=(22, 34, 46), width=1)
    return im, ImageDraw.Draw(im, 'RGBA')


def heading(d, text, y=360, size=48, col=WHITE):
    d.text((W // 2, y), text, font=font(size, 700), fill=col, anchor='mm')
    d.line([(W // 2 - 210, y + 52), (W // 2 + 210, y + 52)], fill=GOLD + (200,), width=3)


def arrow_up(d, x, y0, y1, col, w=10):
    d.line([(x, y0), (x, y1 + 22)], fill=col, width=w)
    d.polygon([(x, y1), (x - 22, y1 + 30), (x + 22, y1 + 30)], fill=col)


def scene_03():
    """熱伝導率の棒グラフ。数値は産総研の一覧（226〜237 / 72〜80.4 W/mK）。"""
    im, d = base()
    heading(d, '熱伝導率（W/mK）')
    d.text((W // 2, 452), '数字が大きいほど、熱をよく伝える', font=font(30, 500), fill=DIM, anchor='mm')

    X0, MAXW, SCALE = 300, 600, 250.0 / 260.0     # 260 W/mK を 600px に
    rows = [('アルミニウム', 226, 237, GOLD, 560), ('鉄', 72, 80.4, BLUE, 800)]
    for name, lo, hi, col, y in rows:
        d.text((X0 - 28, y + 44), name, font=font(38, 700), fill=WHITE, anchor='rm')
        w1, w2 = lo * SCALE, hi * SCALE
        d.rounded_rectangle((X0, y, X0 + w2, y + 88), 10, fill=col + (70,))
        d.rounded_rectangle((X0, y, X0 + w1, y + 88), 10, fill=col + (235,))
        label = ('%g〜%g' % (lo, hi)).replace('.0', '')
        d.text((X0 + w2 + 26, y + 44), label, font=font(40, 700), fill=col, anchor='lm')

    d.text((W // 2, 980), 'アルミ ÷ 鉄 ＝ 約2.8〜3.3倍', font=font(40, 700), fill=WHITE, anchor='mm')
    d.text((W // 2, 1044), '※ 値は文献・材料によって異なる（産総研の一覧にも注記）',
           font=font(26, 500), fill=DIM, anchor='mm')
    im.save(ART / 'scene_03.png')
    print('scene_03.png')


def scene_05():
    """プレートの厚みで、熱の通り方が変わることを示す断面の模式図。"""
    im, d = base()
    heading(d, '同じ素材でも、厚みで変わる')

    for i, (label, thick, note) in enumerate([('厚いプレート', 74, '熱が横にも広がり、\n食材に長く伝わる'),
                                              ('薄いプレート', 22, '熱の広がりが\n小さくなりやすい')]):
        cx = W // 2 + (-1 if i == 0 else 1) * 240
        px0, px1 = cx - 190, cx + 190
        py = 760
        # 食材
        d.rounded_rectangle((px0 + 30, py - 210, px1 - 30, py - 6), 18, fill=(198, 106, 96, 235))
        d.text((cx, py - 108), '食材', font=font(32, 700), fill=(255, 240, 236), anchor='mm')
        # プレート（金属）
        d.rectangle((px0, py, px1, py + thick), fill=(150, 162, 172))
        d.rectangle((px0, py, px1, py + max(6, thick // 5)), fill=(205, 214, 222))
        # 熱の矢印
        for k in (-1, 0, 1):
            arrow_up(d, cx + k * 110, py + thick + 92, py - 4, ORANGE + (235,), 9)
        # ラベル
        d.text((cx, py + thick + 140), label, font=font(36, 700), fill=GOLD if i == 0 else BLUE, anchor='mm')
        d.multiline_text((cx, py + thick + 194), note, font=font(26, 500), fill=DIM, anchor='ma',
                         align='center', spacing=6)

    d.text((W // 2, 520), 'プレートの断面（模式図）', font=font(30, 500), fill=DIM, anchor='mm')
    d.text((W // 2, 1170), '速さの差は、材質・厚み・接触面積・室温で変わる',
           font=font(25, 500), fill=DIM, anchor='mm')
    im.save(ART / 'scene_05.png')
    print('scene_05.png')


def scene_06():
    """プロフィール欄のリンク（楽天ROOM）に商品をまとめている、という案内の模式図。"""
    im, d = base()
    heading(d, '商品名の置き場所')

    px, py, pw, ph = 300, 452, 480, 600
    d.rounded_rectangle((px, py, px + pw, py + ph), 44, fill=(16, 24, 32), outline=(70, 86, 100), width=6)
    d.rounded_rectangle((px + 18, py + 18, px + pw - 18, py + ph - 18), 30, fill=(24, 34, 45))
    # ヘッダ
    d.ellipse((px + 48, py + 56, px + 128, py + 136), fill=(58, 74, 90))
    d.text((px + 148, py + 96), 'チャンネル', font=font(30, 600), fill=WHITE, anchor='lm')
    d.line([(px + 40, py + 172), (px + pw - 40, py + 172)], fill=(60, 76, 92), width=2)
    # リンク行
    d.text((px + 48, py + 226), 'プロフィール', font=font(26, 600), fill=DIM, anchor='lm')
    d.rounded_rectangle((px + 40, py + 262, px + pw - 40, py + 372), 18, fill=(32, 46, 60))
    # 外部リンクの印（絵文字はフォントに無いので「↗」を四角で囲む）
    ix, iy = px + 72, py + 300
    d.rounded_rectangle((ix - 20, iy - 20, ix + 20, iy + 20), 10, outline=GOLD, width=3)
    d.text((ix, iy - 2), '↗', font=font(28, 700), fill=GOLD, anchor='mm')
    d.text((px + 118, py + 300), '楽天ROOM', font=font(34, 700), fill=WHITE, anchor='lm')
    d.text((px + 66, py + 344), '「解凍プレート」で検索', font=font(24, 500), fill=DIM, anchor='lm')
    d.text((px + 48, py + 430), '動画の説明欄のURLは', font=font(24, 500), fill=(140, 152, 164), anchor='lm')
    d.text((px + 48, py + 466), 'タップできないため', font=font(24, 500), fill=(140, 152, 164), anchor='lm')

    # 誘導矢印
    d.line([(W // 2, py + ph + 24), (W // 2, py + ph + 86)], fill=GOLD, width=8)
    d.polygon([(W // 2, py + ph + 122), (W // 2 - 26, py + ph + 76), (W // 2 + 26, py + ph + 76)], fill=GOLD)
    d.text((W // 2, py + ph + 168), 'プロフィールのリンクへ', font=font(36, 700), fill=GOLD, anchor='mm')

    im.save(ART / 'scene_06.png')
    print('scene_06.png')


if __name__ == '__main__':
    scene_03()
    scene_05()
    scene_06()
