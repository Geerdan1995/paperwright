#!/usr/bin/env node
/**
 * 产品沉思录 · 印刷全集 编译器（六卷本）
 *
 * 正文：node scripts/build.mjs --vol 1 --out 卷1-正文
 *   产出 output/<out>.html（正文＋卷末锚点页）与 <out>-anchors.json
 * 前件：node scripts/build.mjs --vol 1 --front --pagemap 卷1-pagemap.json --out 卷1-前件
 *   产出封面＋版权页＋带真实页码的目录
 */
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const OUT_DIR = path.join(ROOT, 'output');
const NM = process.env.PW_FONT_DIR || path.join(ROOT, 'fonts'); // 字体等静态依赖复用手册产线

const argv = process.argv.slice(2);
const arg = (n) => { const i = argv.indexOf(`--${n}`); return i >= 0 ? argv[i + 1] : undefined; };
const vol = Number(arg('vol') || 1);
const isFront = argv.includes('--front');
const pagemapPath = arg('pagemap');
const outName = arg('out') || `卷${vol}`;
const pagemap = pagemapPath ? JSON.parse(fs.readFileSync(path.join(OUT_DIR, path.basename(pagemapPath)), 'utf-8')) : null;

const plan = JSON.parse(fs.readFileSync(path.join(ROOT, 'plan.json'), 'utf-8'));
const V = plan.volumes[vol - 1];
const CN = ['一', '二', '三', '四', '五', '六'];

/* 卷统计 */
const stats = { art: 0, ref: 0, ext: 0, topics: [] };
for (const u of V.units) {
  if (u.type === 'article') stats.art++;
  else if (u.type === 'ref') stats.ref++;
  else if (u.type === 'ext') stats.ext++;
  else if (u.type === 'topichead') stats.topics.push(u.topic);
}

const pg = (a) => (pagemap && pagemap[a] != null ? pagemap[a] : null);
const anchorsOrder = [];
const sigs = {};
const push = (a, title) => { anchorsOrder.push(a); sigs[a] = String(title).replace(/\s+/g, ''); };

/* ---------------- 正文装配 ---------------- */
let body = [];
if (!isFront) {
  for (const u of V.units) {
    if (u.type === 'topichead') {
      const id = `t${V.num}-${u.ji}`;
      body.push(`<section class="topic-opener" id="${id}">
  <div class="to-kicker">第${CN[u.ji - 1]}辑</div>
  <h2 class="to-name">${u.topic}</h2>
  <div class="to-count">${u.total && u.total > u.count ? `本卷 ${u.count} 篇 · 全站 ${u.total} 篇` : `${u.count} 篇`}</div>
  <div class="to-rule"></div>
</section>`);
    } else if (u.type === 'topicindex') {
      body.push(fs.readFileSync(path.join(ROOT, u.file), 'utf-8'));
    } else if (u.type === 'orphans-head') {
      body.push(`<section class="orphans-opener" id="orphans">
  <div class="to-kicker">附录</div>
  <h2 class="to-name">未被正文引用的存档</h2>
  <div class="to-count">${u.count} 篇</div>
  <div class="to-rule"></div>
</section>`);
    } else {
      const frag = fs.readFileSync(path.join(ROOT, u.file), 'utf-8');
      body.push(frag);
      push(u.type === 'article' ? `a${u.id}` : u.type === 'ref' ? `n${u.slug.slice(0, 12)}` : `e${u.id}`, u.title);
    }
  }
}

const auxHtml = `<section class="aux"><h2>·</h2>${anchorsOrder.map((a) => `<a href="#${a}">·</a>`).join('')}</section>`;

/* ---------------- 前件装配 ---------------- */
function tocRows() {
  const groups = [];
  let cur = null;
  for (const u of V.units) {
    if (u.type === 'topichead') {
      cur = { label: `第${CN[u.ji - 1]}辑 · ${u.topic}`, units: [] };
      groups.push(cur);
    } else if (u.type === 'orphans-head') {
      cur = { label: '附录 · 未被正文引用的存档', units: [] };
      groups.push(cur);
    } else if (u.type === 'topicindex') {
      /* 辑内索引不进目录 */
    } else if (cur) {
      const anchor = u.type === 'article' ? `a${u.id}` : u.type === 'ref' ? `n${u.slug.slice(0, 12)}` : `e${u.id}`;
      const last = cur.units[cur.units.length - 1];
      if (u.type === 'article' || !last) cur.units.push([{ anchor, title: u.title }]);
      else last.push({ anchor, title: u.title, sub: true });
    }
  }
  const row = (it) =>
    `<div class="toc-row${it.sub ? ' sub' : ''}"><span class="toc-title">${it.title}</span><span class="toc-dots"></span><span class="toc-pg">${pg(it.anchor) ?? '·'}</span></div>`;
  return groups
    .map((g) => {
      const total = g.units.reduce((n, x) => n + x.length, 0);
      return `<div class="toc-block${total >= 12 ? ' big' : ''}"><div class="toc-group">${g.label}</div>` +
        g.units.map((rows) => `<div class="toc-block">${rows.map(row).join('')}</div>`).join('') + `</div>`;
    })
    .join('');
}

function cover() {
  const topics = stats.topics.map((t) => `<span style="white-space:nowrap">${t}</span>`).join(' · ');
  return `<section class="cover">
  <div class="cover-top"><span>少楠 · fonter 主理</span><span>ARCHIVE EDITION</span></div>
  <div class="cover-title">产品沉思录<br><em>印刷全集</em><span>产品设计通讯的历史文章存档 · 印刷版</span></div>
  <div class="cover-vol-badge">六卷本 · 卷${CN[vol - 1]}｜${V.name}</div>
  <div class="cover-tagline">Read Something Wonderful</div>
  <div class="cover-plate">
    <div class="cp-num"><b>卷${CN[vol - 1]}</b><i>VOL ${vol}</i></div>
    <div class="cp-list">
      <div><b>本卷收录</b>${stats.art} 篇文章 · ${stats.ext} 篇站外转载</div>
      <div><b>内容主题</b>${topics}</div>
    </div>
  </div>
  <div class="cover-main">
    <div class="cover-eyebrow">THE ARCHIVE</div>
    <h3>一份产品通讯的完整存档</h3>
    <p>产品沉思录是由少楠与 fonter 维护的产品设计通讯。本卷收录其历史文章，<br>按主题分卷编排，正文引用的站外原文一并转载，供打印阅读。</p>
  </div>
  <div class="cover-tail">
    <div class="cn">来源 read.pmthinking.com<span class="en">PMTHINKING · 477 ARTICLES</span></div>
    <div class="meta">全集 477 篇中文正文＋中文站外转载<br>编印日期 ${new Date().toLocaleDateString('zh-CN')}</div>
  </div>
</section>`;
}

function colophon() {
  const ledFile = path.join(ROOT, 'fetched', '_ledger.json');
  let extTotal = 0, extOk = 0;
  try {
    const led = JSON.parse(fs.readFileSync(ledFile, 'utf-8'));
    const zh = led.filter((x) => ['weixin', 'douban', 'zhihu'].includes(x.kind));
    extTotal = zh.length; extOk = zh.filter((x) => x.status === 'ok').length;
  } catch { /* 重试未跑完时缺省 */ }
  const extNote = extTotal ? `中文站外原文（微信公众号/知乎/豆瓣）${extTotal} 条成功获取 ${extOk} 条，其余未获取；英文原文一律不收录，仅以「原文链接：域名」注记` : '站外原文获取情况见各篇标注';
  return `<section class="colophon">
  <h2>版权与制作说明</h2>
  <p>本书内容全部来自「产品沉思录」历史文章存档站（read.pmthinking.com）。文章与图片的版权归原作者及产品沉思录（少楠、fonter）所有；站外转载篇目版权归原作者所有，篇前均注明来源。本印刷稿仅供个人学习阅读使用，正文未作内容改写。</p>
  <table class="colophon-table">
    <tr><td>收录口径</td><td>站内正文 477 篇（全量）＋${extNote}；正文内指向站内存档页（/n/）的链接不随书收录，文中以〔存档｜标题〕标示其存在；图片随原文收录</td></tr>
    <tr><td>排序规则</td><td>六卷按题材划分；每篇归入所属主题中最具体的一类（成员最少者优先），卷内分辑，辑内按日期升序；其余所属主题在篇首「也见于」标注。因一篇常属多个主题，各辑末尾附「辑内索引」列出本主题其余成员（标题＋所在卷），全站各主题篇数以站方归档为准</td></tr>
    <tr><td>附件规则</td><td>站外转载全文附于首次引用它的文章之后，篇首注明来源与原文链接；再次引用不重复收录</td></tr>
    <tr><td>日期口径</td><td>均以站方归档标注为准</td></tr>
    <tr><td>本卷卷次</td><td>卷${CN[vol - 1]}｜${V.name}（文章 ${stats.art} · 转载 ${stats.ext}）</td></tr>
    <tr><td>制作日期</td><td>${new Date().toLocaleDateString('zh-CN')}</td></tr>
    <tr><td>版式</td><td>A4 · 宋本（正文思源宋体 12pt / 标题思源黑体）</td></tr>
  </table>
  <p class="colophon-note">「也见于」标签与〔存档〕标记为编者加注，帮助在六卷之间定位内容；其余均为站方原文。</p>
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
    fw('@fontsource/jetbrains-mono', 400),
    css(path.join(ROOT, 'scripts', 'print.css')),
  ].join('\n');
}

fs.mkdirSync(OUT_DIR, { recursive: true });
const title = `产品沉思录 · 印刷全集 卷${CN[vol - 1]}｜${V.name}`;

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
.front .cover { page: fullbleed; }
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
  const html = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>${title} · 正文</title>
${headLinks()}
</head>
<body>
<main class="book">
${body.join('\n')}
${auxHtml}
</main>
</body>
</html>`;
  const outFile = path.join(OUT_DIR, `${outName}.html`);
  fs.writeFileSync(outFile, html, 'utf-8');
  fs.writeFileSync(path.join(OUT_DIR, `${outName}-anchors.json`), JSON.stringify({ anchors: anchorsOrder, sigs }, null, 1), 'utf-8');
  console.log(`✅ body built: ${outFile}`);
  console.log(`   anchors: ${anchorsOrder.length} | ${(Buffer.byteLength(html) / 1024).toFixed(0)} KB`);
}
