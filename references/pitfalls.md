# 印刷排版验收教训（2026-10-19 目录三连改沉淀 + 后续追加）

作者报一个视觉缺陷时，**把同类问题一次找全**：孤行→半页洞→章案例拆散→跨页贴边，四轮全是断页与边距类。对账脚本全过 ≠ 版面没毛病——修完必须渲染相关页逐页目检四边。

## 硬规矩

- **作者实物打印 A4，正文 12pt 起**（10.5pt 被判费眼）；行距 1.7。
- **视觉方案先 HTML 预览判味再动管线**（封面三案、断页方案都走这条路）。
- 修完任何版面类问题：用 PyMuPDF 把相关页渲染成 PNG 逐页看四边，并抽文本层验证关键行在页内。

## 坑账（每条都真实翻过车）

1. **`box-sizing: border-box`**：预览 HTML 带、产线 CSS 没带 → `height:100%` 的框架按内容盒算再叠 padding/border，整框溢出几十 px，底部行被裁出页面。排查法：`'关键词' in page.get_text()` 逐项验证关键内容行在页内；或 Playwright `getBoundingClientRect` 量元素。框架类版式（细框封面、卡片栅格）必须在产线 CSS 补 border-box。
2. **页脚页码模板禁 @page 边距**：`displayHeaderFooter` 的 footerTemplate 与 `@page margin` 冲突会打不出/错位；正文页边距走 `page.pdf({ margin })`，前件满幅页走 `@page fullbleed { margin:0 }` + `preferCSSPageSize: true`。
3. **前件命名页**：封面 fullbleed、其余前件页 `@page { margin: 16mm 0 }`——跨页续页的 padding 不生效，边距必须走 @page（CSS named pages）。
4. **目录断页三规则**：章级原子（章＋其附件/案例永不拆，toc-block 嵌套 atomic）；大组 ≥12 行加 `.big` 可跨页；组头 `break-after: avoid` 不落页底。
5. **卷末锚点索引页（aux）必须极小但可见**：`visibility:hidden` / `height:1mm;overflow:hidden` 会让 Chromium 不生成链接注记，pagemap 链接法直接失效回退到不可靠的文本匹配。锚点多时（>120）用四栏密排，单页装不下溢出到第二页会让 pagemap 只读到最后一页的少量链接（10/145 事故）。
6. **file:// 大文档渲染竞态**：networkidle 会早于页尾脚本解析触发 → `waitUntil:'load'` ＋ `waitForFunction`（无脚本文档按 DOM 实情跳过条件）。纯静态书页等 `document.fonts.ready` ＋ 全部 `img.complete`。
7. **EBUSY**：作者开着 PDF 时重建会失败——写到换名文件（修复版/大字版/v2），交付时提醒关旧开新。
8. **封面深色满版是实物打印系统性缺陷**：全页覆墨、深底条纹、出血边打不出（家用打印机无 borderless）。浅底方案（纸色细框/对切色块）默认入选项；墨量 5%–35% 量级。满铺图记得 `overflow:hidden` 断根（否则 Chromium 打印缩微 96%）。
9. **中文书正文不足 2600 字的"短评"类页面，多半是摘要而非全文**——内容依赖外链的判断要看书长与信号词（全文/翻译自/详见），别只看有没有链接。
10. **paged.js 在 file:// 下起不来**：它用 `fetch()` 拉样式表解析 @page，file:// 被 Chromium 拦 → `ProgressEvent` 报错。解法＝`chromium.launch({ args: ['--allow-file-access-from-files'] })`。
11. **paged.js 手动启动**：`window.PagedConfig={auto:false}`（HTML 内）→ addScriptTag 注入 polyfill → `page.evaluate(() => window.PagedPolyfill.preview())`。等分页完成看 `.pagedjs_pages .pagedjs_page` 数量稳定。
12. **paged 模式页码别走 PDF 解析**：分页器重建 DOM，aux 链接注记法不适用——渲染完直接在页面里 `getElementById` 找所在 `.pagedjs_page` 序号，直测直出 pagemap。同时 assemble 必须加 `--keep-last`（没有 aux 可去）。
13. **paged 与原生分页页数会漂移**（换行策略不同，实测 +7%）：页眉页码书签等全部以当前模式实测为准，两套产物不混用页码。
14. **"改了没生效"诊断法**：位置分毫不变先怀疑 HTML 没重新生成/样式没进产物——`grep 产物文件 新样式特征值`；再用 Playwright `getBoundingClientRect` 量元素真实位置，别靠猜。
15. **封面/封底共用样式放 print.css**（如方案C 的 `.cover-c`），别写在前件内联块——封底单独渲染 HTML 引不到内联样式，会出无样式裸文。
16. **页脚页码视觉居中**：不对称边距（订口宽）下 footerTemplate 全宽居中会偏，用 `margin-left:-6mm` 之类补偿订口与切口差值的一半。
