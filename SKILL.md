---
name: paperwright
description: 把网站/博客/专栏/频道上的既有文章批量装订成"出版级书籍 PDF"：全量爬取→清洗成印刷片段→编辑决策（范围/排序/分卷向用户确认）→封面＋凡例＋带页码目录→两遍法页码对账→合订→逐页目检。四本书验证过的产线。触发词：把这些文章做成书、装订成册、出印刷版、出版级 PDF、书籍级 PDF、成书、合集打印版、博客出书、文章合集 PDF、做成一套书、分卷装订。注意与 print-doc（单篇文档/手册的信息图排版）和 huashu-book-pdf（从零调研写一本新书）的区别：本 skill 的输入是已有网页内容，输出是多章节带目录页码的书。
---

# web-to-book-pdf · 网页内容 → 出版级书籍 PDF

四本书（aliyun 白皮书 430 页、bojeli 专著 393 页、产品沉思录六卷 2801 页、北大课程实录 282 页）验证过的完整产线。所有深度规则、坑账、配方在 `references/`，可直接改装的产线脚本在 `templates/`。

## 第一步永远是：摸底 → 汇报 → 等批准

**范围类决定归用户，一个都不许替他做。** 摸底后必须一次问全（详细口径见 `references/cleaning.md` 编辑决策层）：

1. 收录范围（全量？站内存档？外链内容收不收？）
2. **语种（默认只收与请求者同语言的原文；外文原文件是否收录必须先确认）**
3. 图片进书否；排序规则；多主题归属法；分卷方式
4. 书名（贴请求者原话用词，逐字采用其指定名称）

大件先交**一卷/一册样张**判味，认可后再铺全量。AskUserQuestion 没等到回答 ≠ 同意——停下等。

## 产线八阶段（命令与细节见 `references/pipeline.md`）

```
0 摸底决策   清单/底账 → 摸底报告 → 用户批准（范围/排序/分卷/书名）
1 爬取       urllib 并发 或 templates/fetch-external.cjs（Playwright，登录墙站）
2 清洗       templates/build_fragments 骨架逐站改装 → md/*.html 片段＋plan.json
3 装订编译   build.mjs 多模式：正文(＋aux锚点页) / --paged 正文(页眉页码margin box，无aux) / 前件 / --back 封底
4 渲染       print.cjs（正文带页脚页码；前件/封底 --margin0 满幅）；专业排印走 print-paged.cjs（paged.js）
5 页码       两遍法：pagemap.py 读 aux 链接（须 [links]）；paged 模式由 print-paged 直出 DOM 实测 pagemap
6 合订       assemble.cjs（前件＋正文去aux页［paged 用 --keep-last］＋封底）→ postprocess.py（书签大纲＋目录可点＋元数据）
7 QA交付     页数对账＋抽页PNG看四边＋文本层验证 → 回复附成书绝对路径链接＋打印说明书
```

字体依赖：`export NODE_PATH="$(npm root -g)"`；@fontsource 思源黑宋复用 `D:\Projects\ai-agent-handbook-print\node_modules`。

**字号阶梯与版式呼吸（用户裁决定稿）**：正文 12pt/行距 1.85＋段距 0.6em（段间零距被用户评"课本才这样"）；节标题 15pt/12.5pt 逐级拉开，严禁贴着正文；章扉留白 28mm。完整对照表见 `references/typography.md`——改阶梯必整链重跑（paged 页数漂移大）。

## 迭代纪律

- 用户反馈版面问题：**同类问题一次找全**再改，改完渲染相关页逐页目检四边（`references/pitfalls.md` 开篇）。
- 只重跑受影响链段：改正文→全链重跑；只改封面/目录→前件＋assemble。
- EBUSY＝作者开着 PDF：换名出（修复版/v2），提醒关旧开新。
- 交付时如实声明：抓取失败清单、已知残留、可调点。完整性结论不说满。

## 三条最高频翻车点（其余见 `references/pitfalls.md`）

1. 前件命名页：封面 `@page fullbleed`＋`preferCSSPageSize:true`，其余前件页边距走 `@page`（跨页 padding 不生效）。
2. 卷末 aux 锚点页必须**极小但可见**（hidden 无链接注记；>120 锚点四栏密排防溢出第二页），否则页码链接法失效。paged 模式无 aux，页码由 print-paged.cjs 直测 DOM。
3. 产线 CSS 补 `box-sizing:border-box`——预览 HTML 有、产线没有时框架版式溢出裁底。
4. **目录跨文档锚点会被 Chromium 整条丢弃**：前件里 `#aX` 指向正文，不可点——必须走 postprocess.py 用 fitz 按标题定位行矩形手动插 GoTo 链接（先清旧防重）。
5. paged.js 用 fetch() 解析样式表，file:// 下被拦——Chromium 加 `--allow-file-access-from-files`，`PagedConfig={auto:false}`＋addScriptTag＋手动 `preview()`。
