# Wei You — Personal Research Website

A small, data-driven static site: all content lives in JSON (and markdown for
blog posts), and one command renders the whole website.

```
python3 build.py        # one click: full website in dist/
```

## How it works

```
data/*.json + data/blog/*.md ──► builder/ (load → validate → render → verify) ──► dist/
```

| Path | What it is |
| --- | --- |
| `data/profile.json` | Name, titles, links, bio, education, research interests, GA id |
| `data/papers.json` | Every paper: authors, venue, volume/pages, status, abstract, links |
| `data/talks.json` | Conference and invited talks |
| `data/teaching.json` | Course cards + published course pages |
| `data/team.json` | Current and former students |
| `data/blog/*.md` | Blog posts (markdown with front matter) |
| `templates/site/` | Jinja2 HTML templates (base + pages + partials) |
| `builder/` | The generator: `data.py` (load/validate), `site.py` (render), `checks.py` (verify) |
| `static/` | CSS + JS copied verbatim into `dist/` |
| `assets/` | PDFs, avatar, teaching materials (copied into `dist/assets/`) |
| `dist/` | Build output (gitignored; deployed by GitHub Actions) |
| `CV.tex` / `CV.pdf` | The CV, maintained by hand; the committed PDF is copied into `dist/` |

## Setup (once)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Everyday commands

```bash
python3 build.py            # build the website + run all checks
python3 build.py --serve    # build, then preview at http://localhost:8000
```

Every build validates the data first (missing fields, broken local links,
duplicate ids fail loudly) and verifies the output afterwards (every paper
present on the page, every local link resolving inside `dist/`).

## Common edits

**Add a paper** — append an entry to `data/papers.json`:

```jsonc
{
  "id": "short-unique-slug",
  "type": "working",            // working | journal | conference | thesis
  "year": 2026,
  "title": "Paper Title",
  "topic": "Bandit Learning",   // used for the topic filter
  "authors": ["Coauthor Name", "Wei You"],
  "venue": "Operations Research", // canonical full name; badge label is inferred
  "status": "Under review at Operations Research",  // working papers only
  // for publications instead of status, add citation details:
  // "volume": "74", "number": "2", "pages": "1-20",
  "selected": false,            // true => appears in Home "Selected Papers"
  "abstract": "...",            // inline math with $...$ is fine
  "links": [{ "label": "arXiv", "url": "https://arxiv.org/abs/..." }]
}
```

Optional authorship metadata (kept for reference and future use):
`student_authors`, `alphabetical`, `corresponding`.

Venue badge abbreviations and ranking tiers are inferred from the canonical
full `venue` name using the registry in `builder/config.py`; do not add a
`venue_abbrev` field to paper data. Add new venues to that registry with their
accepted abbreviation and UTD24/FT50 memberships. UTD24 takes precedence when
a journal belongs to both lists. The classifications follow the official
[UTD24 journal list](https://jsom.utdallas.edu/the-utd-top-100-business-school-research-rankings/list-of-journals)
and [FT50 journal list](https://www.ft.com/content/3405a512-5cbb-11e1-8f1f-00144feabdc0).

Use optional `venue_display` only when a citation needs decoration beyond the
canonical name, such as a conference edition or the full thesis wording; it
must retain the canonical name. A working-paper `status` must end with its
canonical venue so the visible review status and venue pill cannot diverge.

**Add a blog post** — create `data/blog/YYYY-MM-DD-slug.md`:

```md
---
title: My New Note
date: 2026-02-10
eyebrow: Research Notes
summary: One-sentence summary shown on the homepage.
tags: [queueing, teaching]
---

Markdown body. Math ($x^2$), code fences, tables, and ```mermaid blocks all work.
```

**Add/maintain a course** — edit `data/teaching.json`. `published: true`
generates `teaching/<slug>.html`; `false` shows a Coming Soon card.

**Talks** — edit `data/talks.json` (`by_coauthor: true` renders the `*` mark).

**Students** — edit `data/team.json` (`status: current|former`; former students
support `thesis` and `placement`).

**Update the CV** — edit `CV.tex`, compile it however you like (e.g.
`latexmk -pdf CV.tex`), and commit the refreshed `CV.pdf`. The build copies
the committed PDF into `dist/CV.pdf`, which the hero "CV" chip links to.

## Deployment

Push to `master`. GitHub Actions (`.github/workflows/pages.yml`) runs
`python3 build.py` and deploys `dist/` to GitHub Pages. Public URLs are
unchanged from the previous site: `/index.html`, `/blogs/<slug>.html`,
`/teaching/<slug>.html`, `/assets/...`, `/CV.pdf`.

Analytics: the GA measurement id lives in `data/profile.json` (`site.ga_id`)
and can be overridden with the `WY_GA_MEASUREMENT_ID` env var.

## Design notes

- Styling lives in a single `static/css/site.css`, organized by design tokens
  (light + dark themes) → base → components → sections. Only widely-supported
  CSS is used; `backdrop-filter` is a progressive enhancement behind
  `@supports`, so the site renders consistently on Safari/Firefox/Chrome/mobile.
- JavaScript is dependency-free and page-scoped: `static/js/site.js` (theme,
  nav, scrollspy, analytics) plus `js/pages/research.js` (filters, search,
  topic grouping, lazy MathJax) and `js/pages/blog_post.js` (TOC highlight,
  copy buttons, Mermaid, highlight.js — all lazy-loaded only when needed).
- Theme preference is stored under the same localStorage keys as before
  (`wy-theme`, `wy-theme-source`), so returning visitors keep their setting.
