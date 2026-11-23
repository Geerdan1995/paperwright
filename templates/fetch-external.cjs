async function main() {
// 站外补抓：微信/豆瓣/知乎/英文源 → fetched/<hash>.json（含清洗后 HTML 与图片本地化）
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const ROOT = path.dirname(path.dirname(__filename));
const jobs = JSON.parse(fs.readFileSync(path.join(ROOT, 'ext_jobs.json'), 'utf-8'));
const IMG_DIR = path.join(ROOT, 'assets', 'img');
fs.mkdirSync(path.join(ROOT, 'fetched'), { recursive: true });
fs.mkdirSync(IMG_DIR, { recursive: true });

const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36';
const hash = (s) => crypto.createHash('md5').update(s).digest('hex').slice(0, 12);

async function saveImages(page, baseHref) {
  // 把页面内的 img 换成本地文件
  const items = await page.evaluate(() => {
    const sel = '#js_content img, .Post-RichTextContainer img, .RichText img, article img, main img';
    return [...document.querySelectorAll(sel)].slice(0, 60).map((im) => {
      const src = im.getAttribute('data-src') || im.getAttribute('src') || '';
      return { src, w: im.naturalWidth || im.width || 0 };
    }).filter((x) => x.src.startsWith('http'));
  });
  const out = [];
  for (const { src } of items) {
    try {
      const resp = await page.request.get(src, { headers: { Referer: baseHref, 'User-Agent': UA }, timeout: 30000 });
      if (!resp.ok()) throw new Error('HTTP ' + resp.status());
      const buf = await resp.body();
      if (buf.length > 8 * 1024 * 1024) throw new Error('too large');
      const fn = 'ext-' + hash(src) + path.extname(new URL(src).pathname).slice(0, 5).replace(/[^.\w]/g, '') || '.jpg';
      const fname = 'ext-' + hash(src) + '.img';
      fs.writeFileSync(path.join(IMG_DIR, fname), buf);
      out.push({ src, file: fname });
    } catch (e) {
      out.push({ src, error: String(e).slice(0, 120) });
    }
  }
  return out;
}

async function extract(page, kind) {
  return await page.evaluate((kind) => {
    const pick = (sels) => { for (const s of sels) { const el = document.querySelector(s); if (el && el.innerText.trim().length > 80) return el; } return null; };
    const title = (document.querySelector('#activity-name, h1.title, h1') || {}).innerText?.trim() || document.title.trim();
    const author = (document.querySelector('#js_name, .ProfileHeader-name, .note-author, meta[name="author"]') || {})?.content || (document.querySelector('#js_name, .ProfileHeader-name, .note-author') || {})?.innerText?.trim() || '';
    if (kind === 'weixin') {
      const c = document.querySelector('#js_content');
      if (!c) return { blocked: !!(document.body.innerText.includes('环境异常') || document.body.innerText.includes('该内容已被发布者删除')), html: null, title, author };
      return { html: c.innerHTML, title, author };
    }
    if (kind === 'zhihu') {
      const c = pick(['.Post-RichTextContainer', '.AnswerCard .RichContent-inner', '.RichContent-inner']);
      return { html: c ? c.innerHTML : null, title, author, blocked: !c };
    }
    if (kind === 'douban') {
      const c = pick(['#link-report .note', '.review-content', '#link-report', '.topic-content', '.status-saying', '.note-container']);
      return { html: c ? c.innerHTML : null, title, author, blocked: !c };
    }
    const c = pick(['article', 'main', '.post-content', '.entry-content', '#content']) || document.body;
    return { html: c.innerHTML, title, author };
  }, kind);
}

const browser = await chromium.launch();
const CONC = 4;
let idx = 0, ok = 0, fail = 0;
const ledger = [];

async function worker(wid) {
  const ctx = await browser.newContext({ userAgent: UA, viewport: { width: 1366, height: 900 }, locale: 'zh-CN', extraHTTPHeaders: { 'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8' } });
  await ctx.addInitScript(() => {
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    window.chrome = { runtime: {}, app: { isInstalled: false } };
    Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en'] });
    Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
    const orig = window.document.createElement;
    window.document.createElement = function (t) { const el = orig.call(this, t); if (t === 'canvas') el.getContext = el.getContext.bind(el); return el; };
  });
  const page = await ctx.newPage();
  while (true) {
    const i = idx++;
    if (i >= jobs.length) break;
    const job = jobs[i];
    const id = hash(job.url);
    const outFile = path.join(ROOT, 'fetched', id + '.json');
    if (fs.existsSync(outFile)) { ok++; continue; }
    let result = { ...job, id, fetchedAt: new Date().toISOString(), status: 'fail', reason: '' };
    for (let attempt = 0; attempt < 2; attempt++) {
      try {
        await page.goto(job.url, { waitUntil: 'domcontentloaded', timeout: 45000 });
        await page.waitForTimeout(kind_wait(job.kind));
        const ext = await extract(page, job.kind);
        if (ext.blocked || !ext.html) {
          result.reason = ext.blocked ? 'blocked(验证墙/已删除/需登录)' : 'no-content';
          if (attempt === 0) { await page.waitForTimeout(4000); continue; }
          break;
        }
        const imgs = await saveImages(page, job.url);
        const html = await page.evaluate(() => location.href);
        result = { ...result, status: 'ok', title: (ext.title || '').trim().slice(0, 200), author: (ext.author || '').trim().slice(0, 80), html: ext.html, imgs, finalUrl: html };
        break;
      } catch (e) {
        result.reason = String(e).split('\n')[0].slice(0, 160);
        if (attempt === 0) await page.waitForTimeout(3000);
      }
    }
    fs.writeFileSync(outFile, JSON.stringify(result));
    if (result.status === 'ok') ok++; else fail++;
    ledger.push({ url: job.url, kind: job.kind, status: result.status, reason: result.reason });
    if ((ok + fail) % 10 === 0) console.log(`  ${ok + fail}/${jobs.length} ok=${ok} fail=${fail}`);
  }
  await ctx.close();
}
function kind_wait(kind) { return kind === 'weixin' ? 3500 : kind === 'zhihu' ? 6000 : kind === 'douban' ? 4000 : 2500; }

await Promise.all(Array.from({ length: CONC }, (_, i) => worker(i)));
await browser.close();
fs.writeFileSync(path.join(ROOT, 'fetched', '_ledger.json'), JSON.stringify(ledger, null, 1));
console.log(`DONE ok=${ok} fail=${fail}`);

}
main().catch(e => { console.error(e); process.exit(1); });
