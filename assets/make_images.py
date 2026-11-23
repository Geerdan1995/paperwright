# -*- coding: utf-8 -*-
"""Paperwright README 图像合成：hero + pages grid（PIL，从真实成书渲染页拼装）"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

SRC = r'D:\Projects\fomalhaut647-print\output'
OUT = os.path.dirname(os.path.abspath(__file__))
PAPER = (245, 241, 230)     # #f5f1e6
INK = (32, 79, 64)          # #204f40
AMBER = (176, 133, 46)      # #b0852e
SHADOW = (60, 60, 55, 60)

def load(name):
    return Image.open(os.path.join(SRC, f'hd-{name}.png')).convert('RGB')

def fit_h(im, h):
    w = int(im.width * h / im.height)
    return im.resize((w, h), Image.LANCZOS)

def paste_with_shadow(base, im, x, y):
    sh = Image.new('RGBA', (im.width + 24, im.height + 24), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sd.rectangle([10, 14, im.width + 14, im.height + 18], fill=SHADOW)
    sh = sh.filter(ImageFilter.GaussianBlur(8))
    base.paste(Image.new('RGB', sh.size, PAPER), (x - 10, y - 10), sh)
    base.paste(im, (x, y))
    return im.width, im.height

def f(size, bold=False):
    p = r'C:\Windows\Fonts\msyhbd.ttc' if bold else r'C:\Windows\Fonts\msyh.ttc'
    return ImageFont.truetype(p, size)

# ---------- hero.png 1568×688 ----------
W, H = 1568, 688
hero = Image.new('RGB', (W, H), PAPER)
d = ImageDraw.Draw(hero)
d.rectangle([0, H - 6, W, H], fill=AMBER)
# 左栏：wordmark＋封面实拍
d.text((84, 56), 'Paperwright 页匠', font=f(44, True), fill=INK)
d.text((88, 138), 'crawl · clean · bind · render · QA', font=f(18), fill=(110, 120, 105))
cover = fit_h(load('cover'), 470)
paste_with_shadow(hero, cover, 90, 176)
# 右栏：标题＋两页实证
d.text((520, 72), 'From a web archive,', font=f(30), fill=(90, 107, 96))
d.text((520, 118), 'to a book you can hold.', font=f(30, True), fill=INK)
d.rectangle([524, 174, 524 + 56, 177], fill=AMBER)
ope = fit_h(load('opener'), 400)
run = fit_h(load('running'), 400)
paste_with_shadow(hero, ope, 520, 216)
paste_with_shadow(hero, run, 520 + ope.width + 60, 216)
d.text((520 + 40, H - 66), 'real output · 354-page PKU course transcripts', font=f(17), fill=(120, 128, 112))
hero.save(os.path.join(OUT, 'hero.png'))
print('hero.png', hero.size)

# ---------- pages.png 1568×720：四联真书页 ----------
W2, H2 = 1568, 720
pg = Image.new('RGB', (W2, H2), (250, 248, 242))
d2 = ImageDraw.Draw(pg)
panels = [('toc', 'Clickable TOC'), ('opener', 'Chapter opener'), ('running', 'Running heads'), ('back', 'Back cover')]
pw = 330
gap = (W2 - pw * 4 - 80) // 3 + 80
x = (W2 - (pw * 4 + gap * 3)) // 2
for name, cap in panels:
    im = fit_h(load(name), 560)
    if im.width > pw:
        im = im.resize((pw, int(im.height * pw / im.width)), Image.LANCZOS)
    xx = x + (pw - im.width) // 2
    paste_with_shadow(pg, im, xx, 64)
    d2.text((x + pw // 2 - len(cap) * 5, 648), cap, font=f(20), fill=INK)
    x += pw + gap
pg.save(os.path.join(OUT, 'pages.png'))
print('pages.png', pg.size)

# ---------- pipeline.svg（项目原生视觉：纸色底/墨绿/杏金） ----------
phases = [
    ('0', 'RECON', 'index · inventory · scope sign-off'),
    ('1', 'CRAWL', 'concurrent fetch · stealth recipes'),
    ('2', 'CLEAN', 'DOM → print fragments · images'),
    ('3', 'BIND', 'front / body / --paged / --back'),
    ('4', 'RENDER', 'Chromium native or paged.js'),
    ('5', 'PAGE-MAP', 'two-pass aux links / DOM-measured'),
    ('6', 'MERGE', 'pdf-lib + outline · clickable TOC'),
    ('7', 'QA', 'edge inspection · text layer'),
]
ph = ['<svg xmlns="http://www.w3.org/2000/svg" width="1568" height="300" viewBox="0 0 1568 300" font-family="Segoe UI, sans-serif">',
      '<rect width="1568" height="300" fill="#f5f1e6"/>',
      '<text x="40" y="52" font-size="26" font-weight="700" fill="#204f40">The pipeline</text>',
      '<rect x="40" y="64" width="46" height="3" fill="#b0852e"/>']
bw, bh, gap2, x2, y2 = 168, 118, 16, 40, 104
for i, (num, name2, desc) in enumerate(phases):
    px = x2 + i * (bw + gap2)
    ph.append(f'<rect x="{px}" y="{y2}" width="{bw}" height="{bh}" rx="10" fill="#ffffff" stroke="#204f4055" stroke-width="1.2"/>')
    ph.append(f'<circle cx="{px + 26}" cy="{y2 + 28}" r="15" fill="#204f40"/>')
    ph.append(f'<text x="{px + 26}" y="{y2 + 33}" font-size="15" fill="#f5f1e6" text-anchor="middle" font-weight="700">{num}</text>')
    ph.append(f'<text x="{px + 50}" y="{y2 + 33}" font-size="16" font-weight="700" fill="#204f40">{name2}</text>')
    words = desc.split(' · ')
    for j, wd in enumerate(words):
        ph.append(f'<text x="{px + 14}" y="{y2 + 62 + j * 19}" font-size="11.5" fill="#5a6b60">{wd}</text>')
    if i < len(phases) - 1:
        ax = px + bw + 2
        ay = y2 + bh // 2
        ph.append(f'<path d="M{ax},{ay - 5} l8,5 l-8,5" fill="none" stroke="#b0852e" stroke-width="2"/>')
        ph.append(f'<line x1="{ax - 6}" y1="{ay}" x2="{ax + 7}" y2="{ay}" stroke="#b0852e" stroke-width="2"/>')
ph.append('</svg>')
open(os.path.join(OUT, 'pipeline.svg'), 'w', encoding='utf-8').write('\n'.join(ph))
print('pipeline.svg', len(ph), 'elements')
