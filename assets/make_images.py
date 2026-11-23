# -*- coding: utf-8 -*-
"""Paperwright README 图像合成 v2：深绿编辑风 hero ＋ 四联真页 ＋ 暗色产线图"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

SRC = r'D:\Projects\fomalhaut647-print\output'
OUT = os.path.dirname(os.path.abspath(__file__))

INK_BG1 = (42, 92, 75)
INK_BG2 = (18, 44, 35)
CREAM = (244, 243, 232)
CREAM_DIM = (201, 214, 192)
AMBER = (227, 194, 115)
DOT = (164, 198, 172)

def f(size, bold=False):
    p = r'C:\Windows\Fonts\msyhbd.ttc' if bold else r'C:\Windows\Fonts\msyh.ttc'
    return ImageFont.truetype(p, size)

def dark_bg(w, h):
    base = Image.new('RGB', (w, h), INK_BG2)
    glow = Image.new('L', (w, h), 0)
    gd = ImageDraw.Draw(glow)
    gd.ellipse([-w * 0.3, -h * 0.55, w * 0.95, h * 0.7], fill=255)
    glow = glow.filter(ImageFilter.GaussianBlur(min(w, h) // 5))
    light = Image.new('RGB', (w, h), INK_BG1)
    return Image.composite(light, base, glow)

def dot_grid(im, alpha=26, step=26):
    ov = Image.new('RGBA', im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for y in range(0, im.height, step):
        for x in range(0, im.width, step):
            d.ellipse([x, y, x + 1.4, y + 1.4], fill=DOT + (alpha,))
    im.paste(Image.alpha_composite(im.convert('RGBA'), ov).convert('RGB'), (0, 0))
    return im

def load(name):
    return Image.open(os.path.join(SRC, f'hd-{name}.png')).convert('RGB')

def fit_h(im, h):
    w = int(im.width * h / im.height)
    return im.resize((w, h), Image.LANCZOS)

def paste_page(base, im, x, y, rot=0):
    pad = 10
    card = Image.new('RGB', (im.width + pad * 2, im.height + pad * 2), CREAM)
    card.paste(im, (pad, pad))
    if rot:
        card = card.rotate(rot, expand=True, resample=Image.BICUBIC)
    card_rgba = card.convert('RGBA')
    sh = Image.new('RGBA', (card.width + 60, card.height + 60), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sd.rectangle([26, 34, card.width + 26, card.height + 26], fill=(0, 0, 0, 110))
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    px, py = x - 24, y - 24
    patch = base.crop((max(0, px), max(0, py), min(base.width, px + sh.width), min(base.height, py + sh.height)))
    base.paste(Image.new('RGB', patch.size, INK_BG2), (max(0, px), max(0, py)), sh.crop((max(0, -px), max(0, -py), max(0, -px) + patch.width, max(0, -py) + patch.height)))
    base.paste(card_rgba, (x, y), card_rgba)
    return card.width, card.height

# ================= hero.png 1568×688 =================
W, H = 1568, 688
hero = dark_bg(W, H)
hero = dot_grid(hero)
d = ImageDraw.Draw(hero)
d.text((W - 640, H - 210), 'PAPERWRIGHT', font=f(64, True), fill=INK_BG2, stroke_width=1, stroke_fill=(96, 130, 108))
paste_page(hero, fit_h(load('cover'), 468), 596, 96, rot=-2)
paste_page(hero, fit_h(load('opener'), 468), 956, 64, rot=1.5)
paste_page(hero, fit_h(load('running'), 468), 1296, 118, rot=-1)
d.text((84, 96), 'Paperwright 页匠', font=f(58, True), fill=CREAM)
d.rectangle([88, 196, 88 + 64, 200], fill=AMBER)
d.text((84, 222), 'From a web archive,', font=f(26), fill=CREAM_DIM)
d.text((84, 264), 'to a book you can hold.', font=f(26, True), fill=CREAM)
d.text((84, 356), '4 books', font=f(30, True), fill=AMBER)
d.text((84, 404), '2,801+ pages produced', font=f(17), fill=CREAM_DIM)
d.text((84, 434), '477-article archive bound in 6 volumes', font=f(17), fill=CREAM_DIM)
d.text((84, H - 96), '0 RECON → 1 CRAWL → 2 CLEAN → 3 BIND → 4 RENDER → 5 PAGE-MAP → 6 MERGE → 7 QA', font=f(15, True), fill=(154, 178, 148))
d.text((84, H - 60), 'real output · 354-page PKU course transcripts', font=f(15), fill=(140, 160, 138))
hero.save(os.path.join(OUT, 'hero.png'))
print('hero.png', hero.size)

# ================= pages.png 1568×720 =================
W2, H2 = 1568, 720
pg = dark_bg(W2, H2)
pg = dot_grid(pg)
d2 = ImageDraw.Draw(pg)
d2.text((48, 42), 'What it makes', font=f(26, True), fill=CREAM)
d2.rectangle([48, 84, 94, 87], fill=AMBER)
panels = [('toc', 'Clickable TOC'), ('opener', 'Chapter opener'), ('running', 'Running heads'), ('back', 'Back cover')]
pw2 = 348
gap2 = (W2 - 96 - pw2 * 4) // 3
x = 48
for name, cap in panels:
    im = fit_h(load(name), 500)
    if im.width > pw2:
        im = im.resize((pw2, int(im.height * pw2 / im.width)), Image.LANCZOS)
    paste_page(pg, im, x + (pw2 - im.width) // 2, 116)
    d2.text((x + 6, 648), cap, font=f(20, True), fill=CREAM_DIM)
    x += pw2 + gap2
pg.save(os.path.join(OUT, 'pages.png'))
print('pages.png', pg.size)

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
bw, bh, gap2, x2, y2 = 168, 118, 16, 40, 104
for i, (num, name2, desc) in enumerate(phases):
    px = x2 + i * (bw + gap2)
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
