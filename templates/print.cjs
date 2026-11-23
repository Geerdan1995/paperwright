/**
 * 产品沉思录 · 印刷全集 PDF 生成器
 * HTML -> A4 PDF（Playwright；正文带页脚页码，前件满幅无页码）
 * 用法：node scripts/print.cjs output/卷1-正文.html [--margin0]
 */
const path = require('path');
const fs = require('fs');
const { pathToFileURL } = require('url');
const { chromium } = require('playwright');
const { PDFDocument } = require('pdf-lib');

const htmlFile = path.resolve(process.argv[2]);
const margin0 = process.argv.includes('--margin0');
const pdfFile = htmlFile.replace(/\.html$/, '.pdf');

(async () => {
  console.log(`🚀 printing: ${path.basename(htmlFile)}${margin0 ? ' [margin0]' : ''}`);
  const browser = await chromium.launch();
  const page = await browser.newPage();

  await page.goto(pathToFileURL(htmlFile).href, { waitUntil: 'load', timeout: 300000 });
  // 本产线正文无脚本；直接等字体与图片
  await page.evaluate(() => document.fonts.ready);
  try {
    await page.waitForFunction(() => [...document.images].every((i) => i.complete), null, { timeout: 90000 });
  } catch { /* 个别图片慢不拦渲染，审计里见 */ }
  await page.waitForTimeout(1500);

  const audit = await page.evaluate(() => {
    const overflows = [];
    for (const el of document.querySelectorAll('pre, table')) {
      if (el.scrollWidth > el.clientWidth + 2) {
        overflows.push(`${el.tagName.toLowerCase()} +${el.scrollWidth - el.clientWidth}px :: ${(el.textContent || '').trim().slice(0, 40)}`);
      }
    }
    const broken = [...document.images].filter((i) => !i.complete || i.naturalWidth === 0).map((i) => i.src.split('/').pop());
    return {
      images: document.images.length,
      broken: broken.slice(0, 12),
      brokenCount: broken.length,
      overflows: overflows.slice(0, 10),
      fontSerif: document.fonts.check('12pt "Noto Serif SC"'),
      fontSans: document.fonts.check('12pt "Noto Sans SC"'),
      units: document.querySelectorAll('section.unit').length,
    };
  });
  console.log('📋 audit:', JSON.stringify(audit, null, 2));

  await page.pdf(
    margin0
      ? { path: pdfFile, format: 'A4', printBackground: true, preferCSSPageSize: true, margin: { top: '0', bottom: '0', left: '0', right: '0' } }
      : {
          path: pdfFile,
          format: 'A4',
          printBackground: true,
          displayHeaderFooter: true,
          headerTemplate: '<span></span>',
          footerTemplate:
            '<div style="font-size:11px;color:#4a4a4a;font-family:Arial,sans-serif;width:100%;text-align:center;padding-top:7mm;margin-left:-6mm;"><span class="pageNumber"></span></div>',
          margin: { top: '22mm', bottom: '20mm', left: '28mm', right: '16mm' },
        },
  );

  await browser.close();
  const doc = await PDFDocument.load(fs.readFileSync(pdfFile));
  const sizeMB = (fs.statSync(pdfFile).size / 1024 / 1024).toFixed(1);
  console.log(`✅ ${pdfFile}`);
  console.log(`   ${doc.getPageCount()} 页 · ${sizeMB} MB`);
})().catch((e) => {
  console.error('❌', e);
  process.exit(1);
});
