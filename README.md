# Paperwright

**Bind web content into print-grade books.**
Turn a blog, newsletter archive, lecture series, or any online article collection into a professionally typeset, print-ready PDF book — with covers, a clickable table of contents, real page numbers, running heads, and multi-volume binding.

> 页匠 — the craftsman who binds the web into books.

`paperwright` is an [Agent Skill](https://agentskills.dev) (SKILL.md format) distilled from **four real production runs** — a 430-page whitepaper, a 393-page technical monograph, a six-volume 2,801-page article archive, and a 354-page lecture transcript collection. Every rule in it was earned by breaking a real book first.

---

## Why not just "print to PDF"?

Browsers print documents. Books are a *system*: asymmetric margins that survive binding, running heads that tell you where you are, chapter openers that breathe, a table of contents whose page numbers are actually correct, a back cover. Paperwright implements that system as a repeatable pipeline, and encodes dozens of print-specific failure modes (see [references/pitfalls.md](references/pitfalls.md)) so you don't rediscover them one ruined print run at a time.

## The pipeline

```
0 RECON      index discovery (llms.txt / embedded JSON / rendered SPA) → inventory → report → user approves scope
1 CRAWL      concurrent fetch (urllib) or headless-browser recipes for login-walled sites
2 CLEAN      per-site DOM → print fragments; image localization; link policies; dedup (bigram + title + sampling)
3 BIND       build modes: body (+aux anchor page) / front matter / --paged body / --back cover
4 RENDER     Playwright print — native mode (footer page numbers) or paged.js pro mode (running heads, margin boxes)
5 PAGEMAP    two-pass page numbers from aux links, or DOM-measured after paged.js
6 MERGE      front + body (+ back cover) via pdf-lib, then postprocess: PDF outline, clickable TOC, metadata
7 QA         page-count audit + per-page edge inspection + text-layer verification → ship with a print spec sheet
```

Full walkthrough: [references/pipeline.md](references/pipeline.md)

## Highlights

- **Two-pass TOC page numbers** — invisible aux anchor page → named-destination extraction → rebuild front matter → merge. Verified `[links]`, never fuzzy text matching.
- **paged.js pro mode** — running heads (book title | chapter title), headerless chapter openers, page numbers as margin boxes. Ships with the polyfill; renders 350+ pages reliably.
- **Clickable TOC + PDF outline + full metadata** — cross-document anchors are silently dropped by Chromium; Paperwright re-inserts real GoTo links with fitz after merging.
- **Book-grade CJK typography** — 12pt body, 1.85 line-height, 0.6em paragraph spacing (indent-only "textbook style" rejected by real readers), justified, orphan/widow control, a full type scale from chapter title to figure caption.
- **Print-first covers** — light "paper frame" system by default; dark full-bleed covers are a known print defect (ink flooding, banding, no-bleed edges) and are offered only on request.
- **Honest fetching** — headless recipes for WeChat / Zhihu / Douban / generic blogs, stealth options, and a failure ledger that is reported *in the book* rather than hidden.
- **Editorial decisions stay with the user** — scope, language, images, ordering, volume split, and the book title are asked up front; a sample volume ships before full production.

## What's inside

```
SKILL.md                 agent-facing entry: decision checklist + 8-phase overview
references/
  pipeline.md            the 8-phase walkthrough with commands
  pitfalls.md            16 earned-the-hard-way failure modes
  cleaning.md            DOM cleaning recipes, link policies, dedup methodology, fetch configs
  cover-systems.md       cover design systems (light paper-frame default, dark on request)
  typography.md          the CJK type scale and its rationale
templates/               production scripts — copy into your project, adapt marked points
  build_fragments_template.py   site HTML → print fragments (★ adaptation points)
  build-single-volume.mjs       4-mode compiler: body / --paged / front / --back
  build-multi-volume.mjs        multi-volume variant (example of a real 6-volume run)
  print.cjs / print-paged.cjs   native & paged.js renderers
  pagemap.py / postprocess.py   two-pass page numbers / outline + clickable TOC + metadata
  assemble.cjs / print.css / fetch-external.cjs / paged.polyfill.js
examples/                notes from three real production runs
```

## Quick start

```bash
# prerequisites
npm install -g playwright pdf-lib && npx playwright install chromium
pip install pymupdf beautifulsoup4 pillow
# fonts (Source Han Sans/Serif via @fontsource) — point this anywhere the packages exist
export PW_FONT_DIR=/path/to/node_modules

# build (from any project directory containing crawl/ and plan.json)
cp -r templates scripts
python scripts/build_fragments.py                       # adapt ★-marked points first
node scripts/build.mjs --paged --out body
node scripts/print-paged.cjs output/body-paged.html --pagemap-out pagemap.json
node scripts/build.mjs --front --pagemap pagemap.json --out front
node scripts/print.cjs output/front.html --margin0
node scripts/build.mjs --back --out back && node scripts/print.cjs output/back.html --margin0
node scripts/assemble.cjs output/front-paged.pdf output/body-paged.pdf book.pdf "Book Title" output/back.pdf --keep-last
python scripts/postprocess.py book.pdf --front output/front-paged.pdf --plan plan.json --pagemap output/pagemap.json \
       --title "Book Title" --author "Source" --subject "Subject" --keywords "a,b"
```

Native (non-paged) mode: drop `--paged`, render the body with `print.cjs`, run `pagemap.py`, and merge without `--keep-last`.

## Using as an agent skill

`SKILL.md` follows the open Agent Skills format. Point any skill-capable agent (ZCode, Claude Code, etc.) at this directory — the skill registers itself and triggers on intents like "把这些文章做成书 / 出印刷版 / 装订成册 / blog → book".

The skill bakes in a hard workflow rule: **recon first, report the inventory, get explicit approval on scope/language/ordering/volume split, ship a sample volume before mass production.** Tools don't get to decide what goes into someone's book.

## Real production runs

| Run | Content | Result |
|---|---|---|
| Enterprise whitepaper | open-source docs site | 430 pp, single volume |
| Technical monograph | mkdocs-based book | 393 pp, single volume |
| Article archive (产品沉思录) | 477 articles + archives + external sources | 6 volumes, 2,801 pp |
| PKU course transcripts | 12 lecture transcripts, ~350k chars | 354 pp, single volume |

Detailed production notes live in `examples/`.

## License

MIT — see [LICENSE](LICENSE). Bundled dependencies keep their own licenses: [Paged.js](https://pagedjs.org) (MIT), [Source Han fonts via @fontsource](https://github.com/fontsource) (OFL).

## 中文

中文说明见 [README.zh-CN.md](README.zh-CN.md)。
