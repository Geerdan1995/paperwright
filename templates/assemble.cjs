/**
 * 装订：前件 PDF（封面/版权/目录）＋ 正文 PDF（去掉卷末锚点索引页）[＋ 封底 PDF] -> 成书
 * 用法（NODE_PATH 需指向全局 npm）：node scripts/assemble.cjs <front.pdf> <body.pdf> <out.pdf> <书名> [封底.pdf]
 */
const fs = require('fs');
const { PDFDocument } = require('pdf-lib');

const [frontFile, bodyFile, outFile, title, backFile] = process.argv.slice(2);
const keepLast = process.argv.includes('--keep-last');   // paged 正文无 aux 页，不去尾

(async () => {
  const front = await PDFDocument.load(fs.readFileSync(frontFile));
  const body = await PDFDocument.load(fs.readFileSync(bodyFile));
  const back = backFile ? await PDFDocument.load(fs.readFileSync(backFile)) : null;

  const book = await PDFDocument.create();
  book.setTitle(title || '印刷版');
  book.setProducer('web-to-book-pdf pipeline');

  const frontPages = await book.copyPages(front, front.getPageIndices());
  frontPages.forEach((p) => book.addPage(p));
  // 非paged正文去掉最后一页（卷末锚点索引，两遍法提取用）
  const bodyIdx = keepLast ? body.getPageIndices() : body.getPageIndices().slice(0, -1);
  const bodyPages = await book.copyPages(body, bodyIdx);
  bodyPages.forEach((p) => book.addPage(p));
  if (back) {
    const backPages = await book.copyPages(back, back.getPageIndices());
    backPages.forEach((p) => book.addPage(p));
  }

  fs.writeFileSync(outFile, await book.save());
  const total = book.getPageCount();
  const sizeMB = (fs.statSync(outFile).size / 1024 / 1024).toFixed(1);
  console.log(`✅ ${outFile}`);
  console.log(`   ${total} 页（前件 ${front.getPageCount()} ＋ 正文 ${bodyIdx.length}${back ? ` ＋ 封底 ${back.getPageCount()}` : ''}）· ${sizeMB} MB`);
})().catch((e) => {
  console.error('❌', e);
  process.exit(1);
});
