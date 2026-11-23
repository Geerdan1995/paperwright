# Paperwright · 页匠

**把网页内容装订成出版级的书。**
博客、通讯存档、课程实录、任何网上的文章合集——做成有封面、可点击目录、真实页码、页眉、可分卷的专业排版 PDF。

> [English](README.md) | 中文

`paperwright` 是一个 [Agent Skill](https://agentskills.dev)（SKILL.md 格式），从**四次真实出书**中沉淀：430 页开源白皮书、393 页技术专著、六卷 2,801 页文章存档全集、354 页课程逐字转写实录。里面的每条规则，都是先在一本真实的书上翻过车才写下来的。

## 为什么不是"打印成 PDF"

浏览器打印的是文档。书是一套**制度**：能扛住装订的不对称版心、告诉你读到哪里的页眉、会呼吸的章扉、页码真的对的目录、封底。Paperwright 把这套制度做成可重复的产线，并且收录了数十种印刷特有的翻车模式（见 [references/pitfalls.md](references/pitfalls.md)），让你不用一次次用报废的打印去重新发现它们。

## 产线八阶段

```
0 摸底      清单发现（llms.txt / 页内序列化 JSON / 渲染 SPA）→ 底账 → 汇报 → 用户批范围
1 爬取      urllib 并发；登录墙站走 Playwright 配方
2 清洗      逐站 DOM → 印刷片段；图片本地化；链接政策；去重（bigram＋标题对撞＋实读抽样）
3 装订      编译四模式：正文(+aux锚点页) / 前件 / --paged 正文 / --back 封底
4 渲染      Playwright——原生模式（页脚页码）或 paged.js 专业模式（页眉双联＋margin box）
5 页码      两遍法读 aux 链接；paged 模式渲染后 DOM 直测
6 合订      pdf-lib 前件＋正文（＋封底）→ postprocess：PDF 书签＋目录可点＋元数据
7 QA        页数对账＋逐页四边目检＋文本层验证 → 随书交付打印说明书
```

详解：[references/pipeline.md](references/pipeline.md)

## 亮点

- **两遍法目录页码**——隐形锚点页 → 命名目标提取 → 重建前件 → 合订。验收必须是 `[links]`，拒绝模糊文本回退。
- **paged.js 专业模式**——页眉双联（书名｜篇名）、章扉免页眉、页码 margin box；自带 polyfill，350+ 页稳定渲染。
- **可点目录＋PDF 书签＋完整元数据**——Chromium 会静默丢弃跨文档锚点，合订后用 fitz 按标题定位行矩形重插真实 GoTo 链接。
- **书级中文排印**——正文 12pt、行距 1.85、段距 0.6em（纯缩进的"课本式"被真实读者否决）、两端对齐、孤字孤行控制、从篇题到图注的完整字号阶梯。
- **打印优先的封面**——默认浅色纸面细框系统；深色满版是已知印刷缺陷（覆墨/条纹/打不出出血边），仅在点名时提供。
- **如实抓取**——微信公众号/知乎/豆瓣/通用博客的无头配方，失败台账直接印在书里，不藏。
- **编辑决定归用户**——收录范围、语种、图片、排序、分卷、书名先问清；先交样册再铺全量。

## 目录结构

```
SKILL.md                 agent 入口：决策清单＋八阶段速览
references/              管线详解 / 坑账 16 条 / 清洗配方 / 封面系统 / 字号阶梯
templates/               13 件产线脚本——拷进项目、改装 ★ 标注点
examples/                三次真实出书的产线笔记
```

## 快速开始

见 [README.md#quick-start](README.md#quick-start)。需要：Node（playwright、pdf-lib 全局）、Python（pymupdf、beautifulsoup4、pillow）、思源黑宋字体（@fontsource）。

## 作为 agent skill 使用

`SKILL.md` 遵循开放 Agent Skills 格式，任何支持 skill 的 agent（ZCode、Claude Code 等）指向本目录即自动注册，触发意图如"把这些文章做成书 / 出印刷版 / 装订成册"。

skill 内建硬规矩：**先摸底、报清单、拿到范围/语种/排序/分卷的明确批准、先交样册再铺全量**——收进用户书里的东西，工具说了不算。

## 真实出书记录

| 战役 | 内容 | 成书 |
|---|---|---|
| 企业白皮书 | 开源文档站 | 430 页 · 全一册 |
| 技术专著 | mkdocs 书 | 393 页 · 全一册 |
| 产品沉思录存档 | 477 篇正文＋存档＋站外原文 | 6 卷 · 2,801 页 |
| 北大课程实录 | 12 篇逐字转写，约 35 万字 | 354 页 · 全一册 |

产线笔记见 `examples/`。

## 协议

MIT——见 [LICENSE](LICENSE)。捆绑依赖保留各自协议：[Paged.js](https://pagedjs.org)（MIT）、[Source Han 字体（@fontsource）](https://github.com/fontsource)（OFL）。
