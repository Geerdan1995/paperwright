# 七阶段产线（每阶段：做什么 · 用什么 · 改哪里）

> 模板在 `../templates/`。字体/依赖：`export NODE_PATH="$(npm root -g)"`（playwright/pdf-lib 全局装），
> `@fontsource/noto-sans-sc · noto-serif-sc · jetbrains-mono` 复用任一既有书项目 node_modules
> （如 `D:\Projects\ai-agent-handbook-print\node_modules`），build.mjs 里 NM 常量指过去。
> 范例项目：`examples/pmthinking (local)\`（多卷＋附件全功能）、`D:\Projects\fomalhaut647-print\`（单册极简＋浅框封面）。

## 阶段 0 · 摸底与决策（先于一切施工）

1. 找全量清单：优先 `llms.txt`；Astro 站挖分类页内序列化转义 JSON（`"id":[0,"…"],"data":[0,{"title":…`，`html.unescape` 后正则提取）；SPA 无静态内容的用 Playwright 渲染后取链接。
2. 试探正文路由（`/blog/<id>` vs `/posts/<id>/` 常见 404/301 试错），curl 一篇看正文是否在初始 HTML（是→urllib 并发爬；否→Playwright 渲染爬）。
3. 建底账：清单（id/标题/日期）、每篇外链/字数/图片、主题归属矩阵，落 `manifest.json` / `inventory.json`。
4. **拿着硬数字向作者汇报，等批准**（见 SKILL.md 决策清单）。摸底报告落盘（如 `摸底报告.md`）。

## 阶段 1 · 爬取

- urllib + ThreadPoolExecutor(12)＋浏览器 UA＋Referer，三次重试；产物 `crawl/<id>.html`。
- 需要登录墙/渲染的站走 `templates/fetch-external.cjs`（Playwright 4 路并发，分域名选择器提取， stealth initScript，失败台账 `fetched/_ledger.json`）。挂死可直接杀，账从 `fetched/*.json` 重建——产物文件齐全就不缺账。

## 阶段 2 · 清洗成片段（`build_fragments.py`，逐站改装）

模板骨架见 `templates/build_fragments.py`（pmthinking 版：文章/存档/转载三类＋附件编排；fomalhaut 版：单类极简）。要点：

- 正文容器定位：常见 `div.prose` / `article` / `main`；先解剖 DOM（元素骨架 Counter＋结构探针）再写规则。
- 标签白名单 BLOCK_OK，白名单外 unwrap；script/style/iframe/nav/aside/header/footer **decompose**。
- 链接三条政策：站内文章 → 「《标题》」文字；站内存档 → 「〔存档｜标题〕」标记；外站 → `span.elink` 保留文字不印 URL（原文链接单独一行印域名）。
- 图片本地化：hash 文件名落 `assets/img/`，附 Referer；超边压缩（PIL，MAX_SIDE≈1600）；丢图记数。
- 站外转载去站头渣：标签级（nav/aside/header/footer）→ 类名黑名单（skip/nav/share/subscribe… 且文本 <200 字）→ 文本黑名单（skip to content/sign in/subscribe）→ 转载标题重复行（归一化后互相包含即删）。无扩展名图片 Chromium 按 magic bytes 渲染，`ext-*.img` 可直接用。
- 产物：`md/*.html` 片段＋`plan.json`（装订计划：卷→辑→单元顺序，附件跟首引文章）。

## 阶段 3 · 装订编译（`build.mjs`）

- 两模式：正文（片段拼接＋卷末 aux 锚点页＋anchors.json 侧车）／前件（封面＋凡例页＋目录，读 pagemap 填真实页码）。
- 前件命名页 CSS：`@page {margin:16mm 0}`、`@page fullbleed {margin:0}`、封面类挂 `page: fullbleed`；**框架类封面补 `box-sizing:border-box`**（pitfalls #1）。
- 目录行＝`toc-row`（标题＋点线＋页码占位），原子块 `toc-block`，≥12 行 `.big` 可拆（pitfalls #4）。
- 多卷版（build-multi-volume.mjs）含辑扉（本卷 N 篇·全站 N 篇）＋辑末双栏索引＋存档补遗附录；单册版（build-single-volume.mjs）砍掉这些层。
- 封面两套见 `cover-systems.md`。

## 阶段 4 · 渲染

**原生模式（`print.cjs`）**——正文页脚页码由 footerTemplate 出：

```
export NODE_PATH="$(npm root -g)"
node scripts/print.cjs output/卷N-正文.html            # 正文：页脚页码
node scripts/print.cjs output/卷N-前件.html --margin0  # 前件：满幅封面
node scripts/print.cjs output/卷N-封底.html --margin0  # 封底（build.mjs --back 出）
```

正文边距**不对称**（单面打印，左订口 28mm／右切口 16mm／上 22mm／下 20mm；页码 footerTemplate `margin-left:-6mm` 补回视觉居中）。

**专业排印模式（`print-paged.cjs`，paged.js）**——页眉双联（左书名/右篇名，`string-set`）、章扉免页眉（`@page chapter:first`）、页码走 `@bottom-center` margin box；未来页下注也走这条路：

```
node scripts/build.mjs --paged --out 全册-正文        # 无 aux；注入 PagedConfig+margin box CSS
node scripts/print-paged.cjs "output/全册-正文-paged.html" --pagemap-out 全册-pagemap.json
```

- Chromium 须 `--allow-file-access-from-files`（paged.js 用 fetch 解析样式表，file:// 被拦）
- `PagedConfig={auto:false}`＋`addScriptTag(paged.polyfill.js)`＋手动 `preview()`
- 页码映射不走 PDF 解析，**渲染完成后在页面里 DOM 直测**（getElementById → 所在 .pagedjs_page 序号）
- 代价：分页器换行策略不同页数会漂移（±7%）、渲染更慢；能接受时优先用（制度感完整）
- 标点挤压/中文标点悬挂是字体整形层的事，paged.js 也不做，如实告知

内置 audit：坏图/溢出/字体检查（brokenCount 必须为 0）。渲染循环耗时 2–10 分钟/卷（paged 更久），放后台跑。

## 阶段 5 · 页码映射

**原生模式**两遍法：`python scripts/pagemap.py 正文.pdf 正文-anchors.json 卷N-pagemap.json` ——
从卷末 aux 页链接注记读命名目标；**必须确认输出 `[links]` 而非 `[text]`**（text 回退有误匹配风险）。链接法覆盖不全时查 aux 溢出（pitfalls #5）。

**paged 模式**：print-paged.cjs 已直测输出 pagemap，跳过此步。

## 阶段 6 · 合订＋后处理

```
node scripts/assemble.cjs 前件.pdf 正文.pdf 成书.pdf 书名 封底.pdf   # paged 正文加 --keep-last（无 aux 可去）
python scripts/postprocess.py 成书.pdf --front 前件.pdf --plan plan.json --pagemap 卷N-pagemap.json \
       --title "书名" --author "来源" --subject "主题" --keywords "k1,k2"
```

postprocess 三件事：**PDF 书签大纲**（封面/凡例/目录＋逐篇，页码＝前件页数＋正文页码）、**目录页可点链接**（跨文档锚点会被 Chromium 丢弃——fitz 按标题前缀定位行矩形手动插 GoTo，先清旧防重）、**元数据补全**（title/author/subject/keywords/creator）。

## 阶段 6 · 合订（`assemble.cjs`）

`node scripts/assemble.cjs 前件.pdf 正文.pdf 成书.pdf 书名` — 前件全部页＋正文去掉最后一页（aux）。EBUSY 就换名出。

## 阶段 7 · QA 与交付

- PyMuPDF：页数对账；抽渲染封面/目录/首篇/附件页 PNG **逐页看四边**（pitfalls 开篇）；文本层验证关键行（页脚页码、凡例行、无残留站头渣）。
- audit 三零：坏图 0、溢出 0、pagemap 链接法满覆盖。
- 交付：**回复附全部成书绝对路径链接**；产线留在项目目录供续册；向作者声明已知的如实注记项（抓取失败清单等）与可调点（排序/封面文案）。
- 迭代循环：用户反馈→改片段/样式→**只重跑受影响链段**（改正文→全链；只改前件→front＋assemble）。
