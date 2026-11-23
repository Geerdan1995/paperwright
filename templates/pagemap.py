# -*- coding: utf-8 -*-
"""
两遍法页码提取：从正文 PDF 卷末锚点索引页的内部跳转链接读出各节起始页。
用法：python scripts/pagemap.py <body.pdf> <anchors.json> <out-pagemap.json>
链接法失败时自动回退文本签名法（按去空白标题逐页顺扫）。
"""
import json, re, sys
import fitz  # PyMuPDF

body_pdf, sidecar, out_json = sys.argv[1], sys.argv[2], sys.argv[3]
meta = json.load(open(sidecar, encoding="utf-8"))
anchors, sigs = meta["anchors"], meta["sigs"]

doc = fitz.open(body_pdf)
result, method = {}, None

# ---- 链接法：卷末索引页的命名目标链接（nameddest=锚点，page=目标页） ----
try:
    last = doc[-1]
    known = set(anchors)
    for l in last.get_links():
        name = l.get("nameddest")
        if name in known and l.get("page", -1) >= 0:
            result[name] = l["page"] + 1
    if len(result) == len(anchors):
        method = "links"
    else:
        print(f"  links covered {len(result)}/{len(anchors)}, falling back")
        result = {}
except Exception as e:
    print("link pass failed:", e)

# ---- 回退：文本签名顺扫 ----
if not result:
    pages_norm = [re.sub(r"\s+", "", p.get_text()) for p in doc]
    cursor = 0
    for a in anchors:
        sig = sigs[a]
        found = None
        for i in range(cursor, len(pages_norm)):
            if sig in pages_norm[i]:
                found = i
                break
        if found is None:
            print(f"  !! sig not found: {a} ({sig})", file=sys.stderr)
            found = cursor
        result[a] = found + 1
        cursor = found
    method = "text"

json.dump(result, open(out_json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"pagemap[{method}]: {len(result)} sections -> {out_json}")
sample = " ".join(f"{k}:{v}" for k, v in list(result.items())[:8])
print("  head:", sample)
