# -*- coding: utf-8 -*-
"""成书后处理：PDF 书签大纲（outline）＋元数据补全
用法：python scripts/postprocess.py 成书.pdf --front 卷N-前件.pdf --plan plan.json --pagemap 卷N-pagemap.json \
       --title "书名" --author "作者/来源" --subject "主题" --keywords "k1,k2"
大纲结构：目录（前件目录页）→ 逐篇（level 1，页码＝前件页数＋正文页码）。多卷书逐卷跑或扩展 plan 解析。"""
import json, re, sys, argparse
import fitz

ap = argparse.ArgumentParser()
ap.add_argument('pdf')
ap.add_argument('--front', required=True, help='前件 PDF（用于页数偏移与目录页定位）')
ap.add_argument('--plan', required=True)
ap.add_argument('--pagemap', required=True)
ap.add_argument('--title')
ap.add_argument('--author')
ap.add_argument('--subject')
ap.add_argument('--keywords')
args = ap.parse_args()

doc = fitz.open(args.pdf)
front = fitz.open(args.front)
offset = front.page_count          # 正文第 1 页＝全书第 offset+1 页
plan = json.load(open(args.plan, encoding='utf-8'))
pagemap = json.load(open(args.pagemap, encoding='utf-8'))

# 目录页＝前件中含「目 录」标题的页（从后往前找，前件尾部）
toc_page = 1
for i in range(front.page_count - 1, -1, -1):
    if '目' in front[i].get_text() and '录' in front[i].get_text():
        toc_page = i + 1
        break

toc = [[1, '封面', 1], [1, '版权与制作说明', 2], [1, '目录', toc_page]]
toc_targets = []   # (标题前缀, 目标页0基) —— 目录页可点链接用
for vol in plan['volumes']:
    cur_level1 = None
    for u in vol['units']:
        if u['type'] == 'topichead':
            cur_level1 = f"第{'一二三四五六七八'[u['ji']-1]}辑 · {u['topic']}" if 'ji' in u else u['topic']
        anchor = None
        if u['type'] == 'article':
            anchor = f"a{u['id']}"
        elif u['type'] == 'ref':
            anchor = f"n{u['slug'][:12]}"
        elif u['type'] == 'ext':
            anchor = f"e{u['id']}"
        if not anchor or anchor not in pagemap:
            continue
        page = offset + pagemap[anchor]
        title = u['title']
        prefix = {'ref': '附｜站内存档', 'ext': '附｜原文转载'}.get(u['type'], '')
        if prefix: title = f'{prefix}｜{title}'
        toc_targets.append((title[:10], page - 1))
        if cur_level1:
            if toc and toc[-1][1] == cur_level1:
                pass
            else:
                toc.append([1, cur_level1, page])
                cur_level1 = None   # 该辑行只记一次（首个成员页）
        toc.append([1, title, page])

doc.set_toc(toc)

# 目录页可点：按标题前缀定位行矩形，插 GoTo 链接（先清旧防重）
tpage = doc[toc_page - 1]
for l in list(tpage.get_links()):
    tpage.delete_link(l)
linked = 0
for needle, target in toc_targets:
    rects = tpage.search_for(needle)
    if rects:
        r = rects[0]
        r = fitz.Rect(r.x0 - 4, r.y0 - 2, tpage.rect.width - 30, r.y1 + 2)  # 整行宽度
        tpage.insert_link({'kind': fitz.LINK_GOTO, 'from': r, 'page': target, 'to': fitz.Point(0, 0)})
        linked += 1
print(f'目录链接 {linked}/{len(toc_targets)}')
meta = {
    'title': args.title or doc.metadata.get('title') or '',
    'author': args.author or '',
    'subject': args.subject or '',
    'keywords': args.keywords or '',
    'creator': 'web-to-book-pdf pipeline',
    'producer': 'Playwright + PyMuPDF',
}
doc.set_metadata({k: v for k, v in meta.items() if v})
doc.saveIncr()
print(f'outline {len(toc)} 条 → {args.pdf}')
for e in toc[:6]: print('  ', e)
