# -*- coding: utf-8 -*-
"""Paperwright README 图像合成 v3：深绿编辑风 hero ＋ 四联真页 ＋ 暗色产线图

渲染纪律（都是踩过的坑）：
- 全程 3x 超采样，最后按整数倍面积平均降采样——旋转边没有锯齿，也不产生振铃暗边
- 页面卡片先建 RGBA 再旋转，fillcolor 用透明——RGB 模式下 rotate 的补角默认是黑的
- 投影由卡片透明通道派生，合成只用 alpha_composite——paste 带 RGBA 蒙版的语义不可靠
- 不做锐化：亮边旁的过冲会看起来像一圈黑线
- finish() 自动验收：卡片以外出现近黑像素即报错——书页照片里的黑是内容，不算
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import sys

SRC = r'D:\Projects\fomalhaut647-print\output'
OUT = os.path.dirname(os.path.abspath(__file__))
S = 3  # supersample factor（须为整数，降采样按整数倍面积平均）

INK_BG1 = (42, 92, 75)
INK_BG2 = (18, 44, 35)
CREAM = (244, 243, 232)
CREAM_DIM = (201, 214, 192)
AMBER = (227, 194, 115)
DOT = (164, 198, 172)
SHADOW = (4, 12, 9)


def f(size, bold=False):
    p = r'C:\Windows\Fonts\msyhbd.ttc' if bold else r'C:\Windows\Fonts\msyh.ttc'
    return ImageFont.truetype(p, size * S)


class Canvas:
    """RGBA 画布＋fp（页面卡片 footprint：卡片内 255，外 0）"""

    def __init__(self, w, h):
        w, h = w * S, h * S
        base = Image.new('RGB', (w, h), INK_BG2)
        glow = Image.new('L', (w, h), 0)
        ImageDraw.Draw(glow).ellipse([-w * 0.3, -h * 0.55, w * 0.95, h * 0.7], fill=255)
        glow = glow.filter(ImageFilter.GaussianBlur(min(w, h) // 5))
        light = Image.new('RGB', (w, h), INK_BG1)
        self.img = Image.composite(light, base, glow).convert('RGBA')
        self.fp = Image.new('L', (w, h), 0)
        self.d = ImageDraw.Draw(self.img)
        # 点阵纹理
        ov = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        r = 0.8 * S
        for y in range(0, h, 26 * S):
            for x in range(0, w, 26 * S):
                od.ellipse([x - r, y - r, x + r, y + r], fill=DOT + (26,))
        self.img.alpha_composite(ov)
        self.d = ImageDraw.Draw(self.img)


def load(name):
    return Image.open(os.path.join(SRC, f'hd-{name}.png')).convert('RGB')


def fit(im, h=None, w=None):
    """按 1x 尺寸缩放到 S 倍画布；坐标以 1x 计，内部乘 S"""
    if h:
        im = im.resize((int(im.width * h * S / im.height), h * S), Image.LANCZOS)
    if w and im.width > w * S:
        im = im.resize((w * S, int(im.height * w * S / im.width)), Image.LANCZOS)
    return im.filter(ImageFilter.GaussianBlur(0.4 * S))  # 压缩细笔画文字的摩尔纹


def paste_page(cv, im, x, y, rot=0):
    """乳白装裱＋微旋转＋柔影。x/y 以 1x 计。"""
    base = cv.img
    x, y = x * S, y * S
    pad = 12 * S
    card = Image.new('RGBA', (im.width + pad * 2, im.height + pad * 2), CREAM + (255,))
    card.paste(im, (pad, pad))
    if rot:
        card = card.rotate(rot, expand=True, resample=Image.BICUBIC, fillcolor=CREAM + (0,))
    alpha = card.split()[3]
    # 投影：卡片透明通道 → 偏移 → 羽化 → 压暗
    sh = Image.new('L', base.size, 0)
    sh.paste(alpha, (x + 12 * S, y + 28 * S))
    sh = sh.filter(ImageFilter.GaussianBlur(28 * S)).point(lambda v: int(v * 0.6))
    shadow = Image.new('RGBA', base.size, SHADOW + (255,))
    shadow.putalpha(sh)
    base.alpha_composite(shadow)
    # 卡片本体（越界部分裁掉再合成）
    x0, y0 = max(0, x), max(0, y)
    cx0, cy0 = x0 - x, y0 - y
    cw = min(card.width - cx0, base.width - x0)
    ch = min(card.height - cy0, base.height - y0)
    box = (cx0, cy0, cx0 + cw, cy0 + ch)
    base.alpha_composite(card.crop(box), (x0, y0))
    cv.fp.paste(alpha.crop(box), (x0, y0), alpha.crop(box))


def finish(cv, name):
    out = cv.img.convert('RGB').resize((cv.img.width // S, cv.img.height // S), Image.BOX)
    fp = cv.fp.resize(out.size, Image.BOX)
    # 验收：卡片以外（含边缘过渡带与投影区）不得有近黑像素
    leaks = [(i % out.width, i // out.width)
             for i, ((r, g, b), a) in enumerate(zip(out.getdata(), fp.getdata()))
             if a < 250 and max(r, g, b) < 16]
    inside_black = sum(1 for (r, g, b), a in zip(out.getdata(), fp.getdata()) if a >= 250 and max(r, g, b) < 16)
    out.save(os.path.join(OUT, name), optimize=True)
    print(f'{name} {out.size} · 卡片外近黑像素 {len(leaks)} · 卡片内（书页内容）近黑像素 {inside_black}')
    if leaks:
        print('   LEAK at', leaks[:12])
        return False
    return True


ok = True

# ================= hero.png 1568×688 =================
W, H = 1568, 688
cv = Canvas(W, H)
d = cv.d
# 幽灵描边字
d.text(((W - 640) * S, (H - 210) * S), 'PAPERWRIGHT', font=f(64, True),
       fill=INK_BG2 + (255,), stroke_width=S, stroke_fill=(96, 130, 108, 255))
# 三页错落
paste_page(cv, fit(load('cover'), 440), 568, 110, rot=-2)
paste_page(cv, fit(load('opener'), 440), 904, 80, rot=1.5)
paste_page(cv, fit(load('running'), 372), 1196, 148, rot=-1)
# 品牌块
d = ImageDraw.Draw(cv.img)
d.text((84 * S, 96 * S), 'Paperwright 页匠', font=f(58, True), fill=CREAM + (255,))
d.rectangle([88 * S, 196 * S, 152 * S, 200 * S], fill=AMBER + (255,))
d.text((84 * S, 222 * S), 'From a web archive,', font=f(26), fill=CREAM_DIM + (255,))
d.text((84 * S, 264 * S), 'to a book you can hold.', font=f(26, True), fill=CREAM + (255,))
d.text((84 * S, 356 * S), '4 books', font=f(30, True), fill=AMBER + (255,))
d.text((84 * S, 404 * S), '2,801+ pages produced', font=f(17), fill=CREAM_DIM + (255,))
d.text((84 * S, 434 * S), '477-article archive bound in 6 volumes', font=f(17), fill=CREAM_DIM + (255,))
d.text((84 * S, (H - 96) * S),
       '0 RECON → 1 CRAWL → 2 CLEAN → 3 BIND → 4 RENDER → 5 PAGE-MAP → 6 MERGE → 7 QA',
       font=f(15, True), fill=(154, 178, 148, 255))
d.text((84 * S, (H - 60) * S), 'real output · 354-page PKU course transcripts',
       font=f(15), fill=(140, 160, 138, 255))
ok &= finish(cv, 'hero.png')

# ================= pages.png 1568×720 =================
W2, H2 = 1568, 720
cv = Canvas(W2, H2)
d2 = cv.d
d2.text((48 * S, 42 * S), 'What it makes', font=f(26, True), fill=CREAM + (255,))
d2.rectangle([48 * S, 84 * S, 94 * S, 87 * S], fill=AMBER + (255,))
panels = [('toc', 'Clickable TOC'), ('opener', 'Chapter opener'),
          ('running', 'Running heads'), ('back', 'Back cover')]
pw2 = 348
gap2 = (W2 - 96 - pw2 * 4) // 3
x = 48
for name, cap in panels:
    im = fit(load(name), 500, pw2)
    paste_page(cv, im, x + (pw2 - im.width // S) // 2, 116)
    d2.text(((x + 6) * S, 648 * S), cap, font=f(20, True), fill=CREAM_DIM + (255,))
    x += pw2 + gap2
ok &= finish(cv, 'pages.png')

# ================= pipeline.svg =================
phases = [
    ('0', 'RECON', 'index · inventory · scope sign-off'),
    ('1', 'CRAWL', 'concurrent fetch · stealth recipes'),
    ('2', 'CLEAN', 'DOM → print fragments · images'),
    ('3', 'BIND', 'front / body / --paged / --back'),
    ('4', 'RENDER', 'Chromium native or paged.js'),
    ('5', 'PAGE-MAP', 'two-pass aux / DOM-measured'),
    ('6', 'MERGE', 'pdf-lib + outline · clickable TOC'),
    ('7', 'QA', 'edge inspection · text layer'),
]
ph = ['<svg xmlns="http://www.w3.org/2000/svg" width="1568" height="300" viewBox="0 0 1568 300" font-family="Segoe UI, sans-serif">',
      '<defs><radialGradient id="g" cx="18%" cy="10%" r="120%">',
      '<stop offset="0%" stop-color="#2a5c4b"/><stop offset="55%" stop-color="#204f40"/><stop offset="100%" stop-color="#122c23"/>',
      '</radialGradient></defs>',
      '<rect width="1568" height="300" fill="url(#g)"/>',
      '<text x="40" y="52" font-size="26" font-weight="700" fill="#f4f3e8">The pipeline</text>',
      '<rect x="40" y="64" width="46" height="3" fill="#e3c273"/>']
bw, bh, gap3, x2, y2 = 168, 118, 16, 40, 104
for i, (num, name2, desc) in enumerate(phases):
    px = x2 + i * (bw + gap3)
    ph.append(f'<rect x="{px}" y="{y2}" width="{bw}" height="{bh}" rx="10" fill="#f4f3e814" stroke="#f4f3e83d" stroke-width="1"/>')
    ph.append(f'<circle cx="{px + 26}" cy="{y2 + 28}" r="15" fill="none" stroke="#e3c273" stroke-width="1.2"/>')
    ph.append(f'<text x="{px + 26}" y="{y2 + 33}" font-size="15" fill="#e3c273" text-anchor="middle" font-weight="700">{num}</text>')
    ph.append(f'<text x="{px + 50}" y="{y2 + 33}" font-size="16" font-weight="700" fill="#f4f3e8">{name2}</text>')
    for j, wd in enumerate(desc.split(' · ')):
        ph.append(f'<text x="{px + 14}" y="{y2 + 62 + j * 19}" font-size="11.5" fill="#a9bfa5">{wd}</text>')
    if i < len(phases) - 1:
        ax = px + bw + 2
        ay = y2 + bh // 2
        ph.append(f'<line x1="{ax - 4}" y1="{ay}" x2="{ax + 8}" y2="{ay}" stroke="#e3c273" stroke-width="2"/>')
        ph.append(f'<path d="M{ax + 8},{ay - 5} l8,5 l-8,5" fill="none" stroke="#e3c273" stroke-width="2"/>')
ph.append('</svg>')
open(os.path.join(OUT, 'pipeline.svg'), 'w', encoding='utf-8').write('\n'.join(ph))
print('pipeline.svg', len(ph), 'elements')

sys.exit(0 if ok else 1)
