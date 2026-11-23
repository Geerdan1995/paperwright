#!/usr/bin/env node
/**
 * fomalhaut647.com《AI 创业与投资》课程实录 · 印刷版编译器（全一册）
 * 正文：node scripts/build.mjs --out 全册-正文
 * 前件：node scripts/build.mjs --front --pagemap 全册-pagemap.json --out 全册-前件
 */
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const OUT_DIR = path.join(ROOT, 'output');
const NM = process.env.PW_FONT_DIR || path.join(ROOT, 'fonts');

const argv = process.argv.slice(2);
const arg = (n) => { const i = argv.indexOf(`--${n}`); return i >= 0 ? argv[i + 1] : undefined; };
const isFront = argv.includes('--front');
const pagemapPath = arg('pagemap');
const outName = arg('out') || '全册';
const pagemap = pagemapPath ? JSON.parse(fs.readFileSync(path.join(OUT_DIR, path.basename(pagemapPath)), 'utf-8')) : null;

const plan = JSON.parse(fs.readFileSync(path.join(ROOT, 'plan.json'), 'utf-8'));
const V = plan.volumes[0];
const pg = (a) => (pagemap && pagemap[a] != null ? pagemap[a] : null);
const anchorsOrder = [];
const sigs = {};
const push = (a, title) => { anchorsOrder.push(a); sigs[a] = String(title).replace(/\s+/g, ''); };

/* ---------------- 正文装配 ---------------- */
let body = [];
if (!isFront) {
  for (const u of V.units) {
    body.push(fs.readFileSync(path.join(ROOT, u.file), 'utf-8'));
    push(`a${u.id}`, u.title);
  }
}
const auxHtml = `<section class="aux"><h2>·</h2>${anchorsOrder.map((a) => `<a href="#${a}">·</a>`).join('')}</section>`;

/* ---------------- 前件装配 ---------------- */
function tocRows() {
  const rows = V.units.map((u) =>
    `<a class="toc-row" href="#a${u.id}"><span class="toc-title">${u.title}</span><span class="toc-dots"></span><span class="toc-pg">${pg(`a${u.id}`) ?? '·'}</span></a>`).join('');
  return `<div class="toc-block"><div class="toc-group">收录篇目</div>${rows}</div>`;
}

function cover() {
  return `<section class="cover-c">
  <div class="frame">
    <div class="top"><span>分享实录 · 全一册</span><span>ARCHIVE EDITION</span></div>
    <div class="center">
      <div class="emblem"><b>12</b><i>PIECES</i></div>
      <h1>AI 创业与投资</h1>
      <div class="h2x">北大分享实录</div>
      <div class="rule"></div>
      <div class="tagline">九场分享，一门新课，三篇随想</div>
      <div class="desc">2026 年秋，北大《AI 创业与投资》课程先后邀请张涛、王淼森、李丰、戴春博、杨锦方、刘勇、朱啸虎、王小川八位嘉宾走进课堂。本册收录全部分享实录、课程介绍与三篇相关随想，据博客 fomalhaut647.com 存档编印。</div>
      <div class="themes">产品创新 · 多模态大模型 · 技术周期 · 风险投资 · 创业框架 · 组织文化</div>
    </div>
    <div class="bottom">
      <div class="src">来源 fomalhaut647.com</div>
      <div class="en">PKU AI STARTUP &amp; INVESTMENT · COURSE ARCHIVE</div>
      <div class="meta">全集 12 篇 · 约 35 万字 · 编印日期 ${new Date().toLocaleDateString('zh-CN')}</div>
    </div>
  </div>
</section>`;
}

function colophon() {
  return `<section class="colophon">
  <h2>版权与制作说明</h2>
  <p>本书内容全部来自个人博客 <strong>fomalhaut647.com</strong> 的课堂实录整理稿，版权归博客作者与各位授课分享嘉宾所有。本印刷稿仅供个人学习阅读使用，正文未作内容改写。</p>
  <table class="colophon-table">
    <tr><td>收录口径</td><td>12 篇全量——9 篇课程分享实录＋1 篇课程介绍＋3 篇随想；按发表时间倒序编排；图片随原文收录</td></tr>
    <tr><td>日期口径</td><td>以站方发布日期为准</td></tr>
    <tr><td>制作日期</td><td>${new Date().toLocaleDateString('zh-CN')}</td></tr>
    <tr><td>版式</td><td>A4 · 宋本（正文思源宋体 12pt / 标题思源黑体）</td></tr>
  </table>
  <p class="colophon-note">篇内「也见于」类标记不存在；正文中的站内链接均转为正文文字，外站链接保留链接文字并以样式区分。</p>
</section>`;
}

function headLinks() {
  const css = (p) => `<link rel="stylesheet" href="${pathToFileURL(p).href}">`;
  const fw = (f, w) => css(path.join(NM, f, `${w}.css`));
  return [
    fw('@fontsource/noto-sans-sc', 400), fw('@fontsource/noto-sans-sc', 500),
    fw('@fontsource/noto-sans-sc', 700),
    fw('@fontsource/noto-serif-sc', 400), fw('@fontsource/noto-serif-sc', 600),
    fw('@fontsource/noto-serif-sc', 700),
    css(path.join(ROOT, 'scripts', 'print.css')),
  ].join('\n');
}

fs.mkdirSync(OUT_DIR, { recursive: true });
const title = 'AI 创业与投资 · 北大分享实录（印刷版）';

if (argv.includes('--back')) {
  const html = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>${title} · 封底</title>
${headLinks()}
<style>
@page { size: A4; margin: 0; }
</style>
</head>
<body>
<section class="cover-c">
  <div class="frame">
    <div class="top"><span>AI 创业与投资 · 北大分享实录</span><span>BACK COVER</span></div>
    <div class="center">
      <div class="h2x" style="margin-top:0">内容简介</div>
      <div class="rule"></div>
      <div class="desc" style="margin-top:0">2026 年秋，北大《AI 创业与投资》课程邀请八位一线创业者与投资人走进课堂：张涛讲 Manus 的诞生与产品创新，王淼森讲多模态大模型，李丰拆解技术趋势与泡沫由来，戴春博谈价值创造，杨锦方谈选人与组织文化，刘勇给出一手创业框架，朱啸虎聊技术周期与风险投资，王小川论主观与客观。</div>
      <div class="desc">本册为逐字转写整理稿，保留课堂问答与现场语境，并附博主三篇相关随想与课程介绍，据博客 fomalhaut647.com 存档编印，仅供个人学习阅读。</div>
      <div class="themes">全一册 · 12 篇 · 约 35 万字 · A4 宋本 12pt</div>
    </div>
    <div class="bottom">
      <div class="src">fomalhaut647.com · 2026</div>
      <div class="en">PKU AI STARTUP &amp; INVESTMENT · COURSE ARCHIVE</div>
      <div class="meta">个人学习打印稿 · 内容版权归原作者所有</div>
    </div>
  </div>
</section>
</body>
</html>`;
  const outFile = path.join(OUT_DIR, `${outName}.html`);
  fs.writeFileSync(outFile, html, 'utf-8');
  console.log(`✅ back cover built: ${outFile}`);
  process.exit(0);
}

if (isFront) {
  const html = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>${title} · 前件</title>
${headLinks()}
<style>
@page { size: A4; margin: 16mm 0; }
@page fullbleed { size: A4; margin: 0; }
.front .cover-c { page: fullbleed; }
</style>
</head>
<body>
<main class="front">
${cover()}
${colophon()}
<section class="toc">
  <h2 class="toc-h">目 录</h2>
  ${tocRows()}
</section>
</main>
</body>
</html>`;
  const outFile = path.join(OUT_DIR, `${outName}.html`);
  fs.writeFileSync(outFile, html, 'utf-8');
  console.log(`✅ front built: ${outFile}`);
} else {
  const isPaged = argv.includes('--paged');
  const pagedBlock = isPaged ? `<style>
/* —— paged.js 排印层：页眉（书名｜篇名）＋页码 margin box＋章首页免页眉 —— */
.unit.article { page: chapter; }
h2.a-title { string-set: chaptitle content(text); }
@page {
  size: A4;
  margin: 26mm 16mm 20mm 28mm;
  @top-left { content: 'AI 创业与投资 · 北大分享实录'; font-family: 'Noto Sans SC', sans-serif; font-size: 7.5pt; color: #8b857a; }
  @top-right { content: string(chaptitle, first); font-family: 'Noto Sans SC', sans-serif; font-size: 7.5pt; color: #8b857a; }
  @bottom-center { content: counter(page); font-family: Arial, sans-serif; font-size: 9pt; color: #4a4a4a; }
}
@page chapter:first {
  @top-left { content: none; }
  @top-right { content: none; }
}
</style>
<script>window.PagedConfig = { auto: false };</script>` : '';
  const html = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>${title} · 正文${isPaged ? '（paged）' : ''}</title>
${headLinks()}
${pagedBlock}
</head>
<body>
<main class="book">
${body.join('\n')}
${isPaged ? '' : auxHtml}
</main>
</body>
</html>`;
  const suffix = isPaged ? '-paged' : '';
  const outFile = path.join(OUT_DIR, `${outName}${suffix}.html`);
  fs.writeFileSync(outFile, html, 'utf-8');
  fs.writeFileSync(path.join(OUT_DIR, `${outName}${suffix}-anchors.json`), JSON.stringify({ anchors: anchorsOrder, sigs }, null, 1), 'utf-8');
  console.log(`✅ body built${isPaged ? ' (paged)' : ''}: ${outFile}`);
  console.log(`   anchors: ${anchorsOrder.length} | ${(Buffer.byteLength(html) / 1024).toFixed(0)} KB`);
}
