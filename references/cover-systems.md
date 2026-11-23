# 封面设计系统（两套＋选型规矩）

> 全部走「先 HTML 预览判味、用户选案再动管线」。预览：三个方案各一个 210×297mm div，
> Playwright 对 `.sheet` 元素逐个 screenshot 出 PNG 交用户选。

## 铁律

- **深色满版封面是实物打印系统性缺陷**（全页覆墨/深底条纹/出血边打不出）。新书封面默认出浅底变体；深色版只在用户点名时给。
- 预览 HTML 有 `* { box-sizing:border-box }`——**搬进产线 CSS 必须一起带**，否则框架类版式溢出裁底（血泪案例见 pitfalls #1）。
- 封面页 `page: fullbleed`；正文流其余页走 `@page` 边距。
- 封面版式类名独立（如 `cover-c`），别复用旧书 `.cover` 类名，避免旧样式串扰。

## 方案C「纸面细框 · 典藏版式」（浅底，墨量≈5%，作者实测选定的打印友好解）

- 结构：米白 `#f5f1e6` 整页 → 内衬 12mm → **双细线框**（`border 1.4pt #1f4738`＋`outline 0.5pt #1f473866`，`outline-offset 2.2mm`）→ 框内上下结构。
- 上：左右分排小字（「分享实录 · 全一册」/「ARCHIVE EDITION」，letter-spacing 3px）。
- 中（居中排版）：杏金圆环徽（`26mm` 圆、`1.2pt solid #b98a2e`，内放篇数＋英文小字）→ 墨绿大标题（`40pt/900/letter-spacing 6px`）→ 杏金衬线副题（`22pt`，`letter-spacing 16px`，需 `text-indent` 补偿尾字距）→ 金线隔断（`30mm×1pt`）→ 衬线标语 → 两端对齐的简介段（`max-width 128mm`）→ 主题串。
- 下（margin-top:auto 贴框底）：来源／英文档案名／篇数·字数·编印日期。
- 完整可用 CSS 在 `D:\Projects\fomalhaut647-print\scripts\build.mjs` 前件 `<style>` 块（方案C 注释段），整段可搬。

## 方案A「纸面反白＋色带收尾」（浅底，墨量≈25%，封面感更强）

米白底全保留 v3 套系元素（空心描边第二行、杏金圆环＋徽章、点阵图版 `radial-gradient` 点阵 `background-size 5.5mm`），底部 1/4 实色绿带（`#204f40`）内装课程介绍块与落款（白字）。适合想要强封面感又能接受少量覆墨的场景。完整 CSS 在 `D:\Projects\fomalhaut647-print\preview\cover-preview.html` 的 `.A` 段。

## v3「深绿满版」（深底，仅用户点名时用）

`radial-gradient(120% 105% at 18% 8%, #2a5c4b, #204f40 46%, #173b30)` 满版；第一行实色＋第二行空心描边（`-webkit-text-stroke: 1.1–1.3pt`）；杏金 `#e3c273`（浅底版文字用深杏金 `#a0781f` 保对比）三处递减强调；点阵图版；衬线标语。范例：`D:\Projects\ai-agent-handbook-print\scripts\print-common.css`。

## 选型话术

给作者的对比表列三列：构成／墨量／气质；附 PNG 预览链接；给推荐但让作者拍板。混血变体（如细框＋绿带）按需出。
