# -*- coding: utf-8 -*-
r"""build_fragments 骨架模板：爬取产物 → 印刷片段 + plan.json
★改点 标注处按目标站改装。完整实战例：examples/pmthinking (local)\scripts\build_fragments.py（多类单元＋附件编排）
                 D:\Projects\fomalhaut647-print\scripts\build_fragments.py（单类极简＋hero 图）"""
import re, json, os, hashlib, time, urllib.request
from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD = os.path.join(ROOT, 'md'); os.makedirs(MD, exist_ok=True)
IMG_DIR = os.path.join(ROOT, 'assets', 'img'); os.makedirs(IMG_DIR, exist_ok=True)

# ★改点：装订顺序（单元 id 按作者批的排序规则排好）
ORDER = []          # 例：['lecture-zhang-tao', ...]
man = {}            # ★改点：从 manifest.json 读 {id: {title, date, ...}}

BLOCK_OK = {'p','ul','ol','li','strong','em','b','i','blockquote','figure','img','br','hr',
            'table','thead','tbody','tr','th','td','code','pre','h2','h3','h4','sup','sub','a','span'}
lost_imgs = 0

def img_local(src):
    """★改点：图片本地化（相对/绝对 URL、Referer、超边压缩可选）"""
    global lost_imgs
    src = src.replace('&amp;', '&')
    if src.startswith('/'): src = 'https://目标站' + src
    if not src.startswith('http'): return None
    name = hashlib.md5(src.encode()).hexdigest() + os.path.splitext(src.split('?')[0])[1][:5]
    out = os.path.join(IMG_DIR, name)
    if not os.path.exists(out):
        req = urllib.request.Request(src, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://目标站/'})
        for a in range(3):
            try:
                with urllib.request.urlopen(req, timeout=40) as r:
                    open(out, 'wb').write(r.read())
                break
            except Exception:
                time.sleep(1 + a)
        else:
            lost_imgs += 1
            return None
    return f'../assets/img/{name}'

def fmt_date(iso):
    m = re.match(r'(\d{4})-(\d{2})-(\d{2})', iso or '')
    return f'{m.group(1)} 年 {int(m.group(2))} 月 {int(m.group(3))} 日' if m else (iso or '')

def article_fragment(aid):
    meta = man[aid]
    html = open(f'{ROOT}/crawl/{aid}.html', encoding='utf-8').read()
    # ★改点：hero 封面图（如有）——在正文容器之前定位
    hero_loc = None
    # ★改点：正文容器选择器（先解剖 DOM：元素骨架 Counter + 结构探针）
    m = re.search(r'<div[^>]*class="[^"]*prose[^"]*"[^>]*>', html)
    end = html.find('</main>', m.end())
    soup = BeautifulSoup(html[m.end():end], 'html.parser')
    # 标签级清理（decompose 的都是确定性垃圾）
    for t in soup.find_all(['script','style','iframe','form','button','input','video','audio','svg','noscript','nav','aside','header','footer']):
        t.decompose()
    # ★站点标题锚点图标（网页悬停用的 #，markdown-it-anchor / 各框架 hero anchor）：印刷态删除
    for t in soup.find_all(class_=re.compile(r'anchor', re.I)):
        t.decompose()
    for t in soup.find_all('a'):
        if t.get_text(strip=True) == '#': t.decompose()
    # 图片本地化
    for t in soup.find_all('img'):
        loc = img_local(t.get('data-src') or t.get('src') or '')
        if loc:
            t.attrs = {'src': loc, 'alt': (t.get('alt') or '')[:60]}
            par = t.find_parent()
            if par is not None and par.name == 'figure': par['class'] = 'a-fig'
        else:
            t.decompose()
    # 白名单外 unwrap；标题降级（书内篇题占 h2）；链接转文字
    for t in soup.find_all(True):
        if t.name not in BLOCK_OK: t.unwrap()
    for t in list(soup.find_all('h3')): t.name = 'h4'
    for t in list(soup.find_all('h2')): t.name = 'h3'
    for t in soup.find_all('a'):
        t.name = 'span'; t.attrs = {'class': 'elink'}
    # ★改点：站内互引转「《标题》」、存档链接转「〔存档｜标题〕」（见 references/cleaning.md 链接政策）
    # 属性清空（图片除外）；空节点删除
    for t in soup.find_all(True):
        if t.name != 'img': t.attrs = {}
    for t in soup.find_all(['p','ul','ol','figure','blockquote','li','span','td','th','h3','h4']):
        if not t.get_text(strip=True) and not t.find('img'): t.decompose()
    # ★兜底：标题尾部残留的 #（部分源站标题自带或清洗后残余）
    for h in soup.find_all(['h3','h4']):
        for node in reversed(list(h.children)):
            if isinstance(node, str):
                s = str(node).rstrip()
                if s.endswith('#'):
                    node.replace_with(node.replace('#', ''))
                    break
                if s: break
            else:
                break
    # ★改点：篇头组装（tags/byline 字段按站点元数据取）
    h = [f'<section class="unit article" id="a{aid}">', '<header class="a-head">']
    h.append(f'<h2 class="a-title">{meta["title"]}</h2>')
    h.append(f'<div class="a-byline"><span>{fmt_date(meta["published"])}</span></div></header>')
    if hero_loc: h.append(f'<figure class="a-hero"><img src="{hero_loc}" alt=""></figure>')
    h.append(f'<div class="a-body">{soup}</div>')
    h.append('</section>')
    return '\n'.join(h)

units = []
for aid in ORDER:
    open(f'{MD}/art-{aid}.html', 'w', encoding='utf-8').write(article_fragment(aid))
    units.append({'type': 'article', 'id': aid, 'title': man[aid]['title'], 'file': f'md/art-{aid}.html'})
    print('ok', aid)

json.dump({'volumes': [{'num': 1, 'name': '全一册', 'units': units, 'n_articles': len(units)}]},
          open(f'{ROOT}/plan.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'共 {len(units)} 篇，丢失图片 {lost_imgs}')
