# templates/ 使用说明

这些是四本书验证过的产线脚本原件，**整目录拷进新书项目 `scripts/` 后按 ★改点 改装**。

| 文件 | 用途 | ★改点 |
|---|---|---|
| `build_fragments_template.py` | 爬取产物 → 印刷片段＋plan.json | 正文容器选择器、链接政策、篇序 kicker、图注编号、清单字段 |
| `build-single-volume.mjs` | **单册书全功能编译器**：正文/`--paged`/前件/`--back` 封底 四模式＋方案C封面＋凡例＋可点目录 | 封面/封底文案、凡例表、NM 字体路径、paged 页眉书名 |
| `build-multi-volume.mjs` | 多卷书装订编译器（辑扉＋辑内索引＋存档附录＋凡例；**尚未并入批二/批三升级**，需按 single-volume 版对齐后用） | 卷定义 VOLUMES、封面文案、凡例表、NM 字体路径 |
| `print.cjs` | Playwright 渲染原生模式（不对称版心 28/16/22/20＋页脚页码补偿；--margin0 满幅）＋audit | 一般不用改 |
| `print-paged.cjs` | **paged.js 专业排印渲染**（页眉双联＋章扉免页眉＋页码 margin box＋DOM 直测 pagemap） | 页眉书名字串、polyfill 路径 |
| `paged.polyfill.js` | paged.js v0.4.3 本体（技能自带，离线可用） | 不改 |
| `pagemap.py` | 原生模式两遍法页码提取（链接法→文本回退） | 不用改；看输出必须是 `[links]` |
| `postprocess.py` | 成书后处理：**PDF 书签大纲＋目录页可点链接（fitz 定位行矩形插 GoTo）＋元数据补全** | 一般不用改 |
| `assemble.cjs` | 合订：前件＋正文（去 aux；paged 用 `--keep-last`）＋可选封底 | 书名元数据 |
| `print.css` | 全套版式：A4 宋本 12pt 两端对齐＋孤行控制／章扉 kicker／图注／目录／封面封底方案C／aux | 新书可选删未用段 |
| `fetch-external.cjs` | Playwright 站外抓取（微信/知乎/豆瓣/通用配方＋stealth） | 任务清单字段；分域名选择器按需增 |

## 通用前置

```bash
export NODE_PATH="$(npm root -g)"   # playwright / pdf-lib 全局
```

字体：build.mjs 的 `NM` 常量指向 `D:\Projects\ai-agent-handbook-print\node_modules`
（@fontsource/noto-sans-sc · noto-serif-sc · jetbrains-mono）。独立环境则需自装这些包。

## 标准链路（单册 · 专业排印 paged 模式）

```bash
python scripts/build_fragments.py
export NODE_PATH="$(npm root -g)"
node scripts/build.mjs --paged --out 全册-正文                                  # 正文（页眉/页码 margin box，无 aux）
node scripts/print-paged.cjs "output/全册-正文-paged.html" --pagemap-out 全册-pagemap.json
node scripts/build.mjs --front --pagemap 全册-pagemap.json --out 全册-前件      # 封面＋凡例＋可点目录
node scripts/print.cjs "output/全册-前件.html" --margin0
node scripts/build.mjs --back --out 全册-封底 && node scripts/print.cjs "output/全册-封底.html" --margin0
node scripts/assemble.cjs output/全册-前件.pdf output/全册-正文-paged.pdf \
     output/成书.pdf "书名" output/全册-封底.pdf --keep-last
python scripts/postprocess.py output/成书.pdf --front output/全册-前件.pdf \
     --plan plan.json --pagemap output/全册-pagemap.json \
     --title "书名" --author "来源" --subject "主题" --keywords "k1,k2"
```

原生模式（不用 paged）：`--paged` 去掉、正文走 `print.cjs`＋`pagemap.py` 两遍法、assemble 去掉 `--keep-last`。多卷在单册链路外套 `for v in ...` 循环（build-multi-volume.mjs，注意其对齐提示）。

## 注意

- build_fragments_template.py 是骨架，**站点差异全在正文容器选择器与清洗规则**——先解剖 DOM 再动手（见 references/cleaning.md）。
- fetch-external.cjs 是 ESM 逻辑但以 `.cjs` 提供（ESM import 不认 NODE_PATH）；模板内已包 `main()`。
- EBUSY＝作者开着 PDF：输出换名。
- 每次正文变动 → 全链重跑；只动封面/目录 → 仅前件＋assemble＋postprocess。


## 注意

- build_fragments_template.py 是骨架，**站点差异全在正文容器选择器与清洗规则**——先解剖 DOM 再动手（见 references/cleaning.md）。
- fetch-external.cjs 是 ESM 逻辑但以 `.cjs` 提供（ESM import 不认 NODE_PATH）；模板内已包 `main()`。
- EBUSY＝作者开着 PDF：输出换名。
