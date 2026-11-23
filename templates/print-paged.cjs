/**
 * paged.js 专业排印渲染器：正文 HTML → PDF ＋ DOM 直测页码映射
 * 收益：页眉（书名｜篇名，章首页免页眉）、页码 margin box、章扉制度、（可扩展页下注）
 * 用法：NODE_PATH=全局 node scripts/print-paged.cjs output/卷N-正文-paged.html [--pagemap-out 卷N-pagemap.json]
 * 前置：HTML 内已带 @page margin box 规则；输出目录有 paged.polyfill.js（../scripts/）
 */
const path = require('path');
const fs = require('fs');
const { pathToFileURL } = require('url');
const { chromium } = require('playwright');
const { PDFDocument } = require('pdf-lib');

const htmlFile = path.resolve(process.argv[2]);
const pagemapOutIdx = process.argv.indexOf('--pagemap-out');
const pagemapOut = pagemapOutIdx >= 0 ? process.argv[pagemapOutIdx + 1] : null;
const pdfFile = htmlFile.replace(/\.html$/, '.pdf');

(async () => {
  console.log(`🚀 printing (paged.js): ${path.basename(htmlFile)}`);
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  const page = await browser.newPage();

  await page.goto(pathToFileURL(htmlFile).href, { waitUntil: 'load', timeout: 300000 });
  await page.evaluate(() => document.fonts.ready);

  // 注入 polyfill 并手动启动（auto:false 由 HTML 内 PagedConfig 设定）
  await page.addScriptTag({ path: path.join(path.dirname(htmlFile).replace(/output$/, ''), 'scripts', 'paged.polyfill.js') });
  await page.evaluate(() => window.PagedPolyfill.preview()).catch((e) => {
    console.error('   preview 报错（继续检查产物）:', e.message || e);
  });

  // 等分页完成：页数稳定
  await page.waitForFunction(() => {
    const pages = document.querySelectorAll('.pagedjs_pages .pagedjs_page');
    return window.__pagedDone === true || (pages.length > 0 && !document.querySelector('.pagedjs_footnote__container:not(:empty)') && window.__pagedGenerating !== true);
  }, null, { timeout: 600000, polling: 1000 });
  await page.waitForTimeout(1500);

  const pageCount = await page.evaluate(() => document.querySelectorAll('.pagedjs_pages .pagedjs_page').length);
  console.log(`   paged.js 分页完成：${pageCount} 页`);

  // DOM 直测锚点→页码（替代 PDF 链接注记解析；锚点清单来自 build.mjs 的 anchors.json 侧车）
  if (pagemapOut) {
    const sidecar = htmlFile.replace(/\.html$/, '-anchors.json');
    const anchorIds = fs.existsSync(sidecar) ? JSON.parse(fs.readFileSync(sidecar, 'utf-8')).anchors : [];
    const anchors = await page.evaluate((ids) => {
      const pages = [...document.querySelectorAll('.pagedjs_pages .pagedjs_page')];
      const map = {};
      for (const id of ids) {
        const el = document.getElementById(id);
        if (!el) continue;
        let node = el, pageIdx = -1;
        while (node) {
          if (node.classList && node.classList.contains('pagedjs_page')) { pageIdx = pages.indexOf(node); break; }
          node = node.parentElement;
        }
        if (pageIdx >= 0) map[id] = pageIdx + 1;
      }
      return map;
    }, anchorIds);
    fs.writeFileSync(path.join(path.dirname(pdfFile), pagemapOut), JSON.stringify(anchors, null, 1), 'utf-8');
    console.log(`   pagemap(DOM 直测): ${Object.keys(anchors).length}/${anchorIds.length} 锚点 → ${pagemapOut}`);
  }

  await page.pdf({ path: pdfFile, width: '210mm', height: '297mm', printBackground: true, margin: { top: 0, bottom: 0, left: 0, right: 0 } });

  const audit = await page.evaluate(() => ({
    pages: document.querySelectorAll('.pagedjs_pages .pagedjs_page').length,
    images: document.images.length,
    broken: [...document.images].filter((i) => !i.complete || i.naturalWidth === 0).length,
  }));
  console.log('📋 audit:', JSON.stringify(audit));

  await browser.close();
  const doc = await PDFDocument.load(fs.readFileSync(pdfFile));
  console.log(`✅ ${pdfFile}`);
  console.log(`   ${doc.getPageCount()} 页 · ${(fs.statSync(pdfFile).size / 1024 / 1024).toFixed(1)} MB`);
})().catch((e) => {
  console.error('❌', e);
  process.exit(1);
});
