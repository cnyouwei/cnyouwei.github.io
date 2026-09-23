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
| `data/profile.json` | Name, titles, links, bio, education, avatar/share image, research interests, canonical URL, GA id |
| `data/papers.json` | Every paper: authors, optional venue, volume/pages, status, abstract, links |
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
| `tests/` | Python regression tests and development-only browser smoke tests |

## Setup (once)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --require-hashes -r requirements.txt
```

## Everyday commands

```bash
python3 build.py            # build the website + run all checks
python3 build.py --serve    # build, then preview at http://localhost:8000
```

Every build validates content types, required metadata, dates, slugs, and URL
schemes before rendering. It then checks generated pages, unique IDs, local
files and HTML fragments. The preview server binds
to `127.0.0.1` by default; `--port 8001` selects a different local port. Use
`--host` explicitly if you intend to expose a preview on another interface.

## Verification

Use Python 3.12 or newer. The production install does not require browser tools.
For changes to the generator, templates, styling, or JavaScript:

```bash
python -m pip install --require-hashes -r requirements-dev.txt
python -m playwright install chromium
python -m unittest discover -s tests -p 'test_*.py'
python build.py
python tests/browser_smoke.py
python tests/browser_smoke.py --live-dependencies
```

The regular browser suite uses deterministic dependency fixtures to exercise
loading failures and recovery. The live mode requires network access and checks
the real MathJax, Mermaid, and highlighting assets; an unavailable renderer is
reported as a failure. Both commands start and stop their own local preview.
Tests enforce the site's Content Security Policy throughout. Analytics-origin
checks intercept every request and never send analytics to Google.

The Chromium matrix discovers content pages from the sitemap plus the custom
404, with eight widths from 320 to 1440px and both themes. Additional cases cover 200% text
enlargement and CSS zoom, keyboard/touch controls, complete print output and
view restoration, no-JavaScript navigation, and delayed or failed renderers.
CSS zoom is an emulation; it does not drive the browser's own zoom control.

Dependency input files declare direct packages; the corresponding `.txt` files
lock the resolved versions and hashes. Review updates together with their lock
changes and run the complete suite before merging. Browser tooling is confined
to development requirements.

To refresh the locks as a maintainer:

```bash
python -m pip install pip-tools==7.5.3
python -P -m piptools compile --upgrade --generate-hashes --strip-extras --output-file=requirements.txt requirements.in
python -P -m piptools compile --upgrade --generate-hashes --strip-extras --output-file=requirements-dev.txt requirements-dev.in
```

The `-P` flag prevents this repository's `build.py` from shadowing pip-tools'
own build dependency. Regenerate the production lock first; the development
lock is constrained to the same production package versions.

## Common edits

Routine updates use the five content JSON files in `data/` and the independently
maintained CV. Blog text lives in `data/blog/`; add any new linked PDFs or images
under `assets/`. The generator builds the current content from these sources.

**Add a paper** — append an entry to `data/papers.json`:

```jsonc
{
  "id": "short-unique-slug",
  "type": "working",            // working | journal | conference | thesis
  "year": 2026,
  "title": "Paper Title",
  "topic": "Bandit Learning",   // used for the topic filter
  "authors": ["Coauthor Name", "Wei You"],
  "venue": "Operations Research", // optional canonical name; badge label is inferred
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

When a venue has not been specified, omit `venue` or set it to `null`. The
paper will render without a venue pill. Empty strings and unknown non-empty
venue names remain invalid so mistakes fail during the build.

Use optional `venue_display` only when a citation needs decoration beyond the
canonical name, such as a conference edition or the full thesis wording; it
must retain the canonical name and cannot be used without `venue`. When a
working paper has a venue, its `status` must end with that canonical venue so
the visible review status and venue pill cannot diverge.

**Add a blog post** — create `data/blog/YYYY-MM-DD-slug.md`:

````md
---
title: My New Note
date: 2026-02-10
eyebrow: Research Notes
summary: One-sentence summary shown on the homepage.
tags: [queueing, teaching]
---

Markdown body. Math ($x^2$), code fences, tables, and ```mermaid blocks all work.
````

Every post requires nonempty `title`, `date`, and `summary` front-matter fields;
dates must be valid calendar dates in `YYYY-MM-DD` form. Page slugs are single filename
segments containing letters, digits, underscores, or hyphens. Keep an existing
slug unchanged to preserve links. Mathematical notation is handled by Arithmatex
before heading navigation is generated; normal code fences remain literal.

**Add/maintain a course** — edit `data/teaching.json`. `published: true`
generates `teaching/<slug>.html`; `false` shows a Coming Soon card.

**Talks** — edit `data/talks.json` (`by_coauthor: true` renders the `*` mark).

**Students** — edit `data/team.json` (`status: current|former`; former students
support `thesis` and `placement`).

**Update the CV** — edit `CV.tex`, compile it however you like (e.g.
`latexmk -pdf CV.tex`), and commit the refreshed `CV.pdf`. The build copies
the committed PDF into `dist/CV.pdf`, which the hero "CV" chip links to.

## Deployment

Pull requests run validation without deployment permissions. Trusted branch
builds run the same checks before GitHub Pages deployment. Deployment permissions
are restricted to the deploy job; dependency installation and tests do not need
Pages or OIDC write access.

The public site remains at `https://cnyouwei.github.io`. Each build replaces
`dist/` with the current homepage, blog and course pages, assets, CV, and site
metadata. PDFs are published once at their current paths under `assets/`, with
the CV at `/CV.pdf`. Old standalone section URLs and `/papers/` aliases are no
longer generated. Use current section anchors such as `/index.html#talks` and
current download URLs when sharing links.

Every published PDF must be linked from a generated page or explicitly retained
in `PUBLISHED_UNLINKED_PDFS` in `builder/config.py`. That inventory preserves
existing legacy URLs; new unlinked drafts fail the build. Images and fonts can
be referenced indirectly by CSS or scripts and are not subject to this PDF check.

The build also emits canonical/social metadata, a sitemap, robots instructions,
and a custom 404 page. `site.base_url` supplies the canonical origin; it must
match the production site when changing domains.

`avatar.src` is the optimized portrait. Optional `avatar.share_src` supplies a
JPEG of the same dimensions for social previews; it falls back to the portrait.
The homepage also emits Person structured data from the existing profile.

Analytics: the GA measurement id lives in `data/profile.json` (`site.ga_id`)
and can be overridden with the `WY_GA_MEASUREMENT_ID` env var. Analytics loads
only on the configured production hostname. Keep the ID empty to disable it.
The integration retains its existing automatic page-view behavior; it does not
implement a visitor consent interface.

## Content and safety

Website JSON and the CV are maintained independently. Review both when updating
courses, students, or publications, then rebuild the site and regenerate the CV
PDF when its source changes.

Blog Markdown supports authored HTML, so repository contributors are trusted
content authors. Ordinary template values are escaped, URL schemes are checked,
and Mermaid uses strict mode. These controls do not turn the builder into a
safe processor for arbitrary uploaded HTML.

External browser dependencies are deliberately limited:

| Service | Purpose and behavior |
| --- | --- |
| Google Fonts | Fraunces and Inter, plus a two-character Chinese name subset on the homepage; system fonts provide a fallback |
| jsDelivr | Pinned MathJax, Mermaid, and highlight.js; versions and URLs live in `builder/config.py` |
| Google Analytics | Optional production-only page analytics, controlled by `site.ga_id` or the environment override |

Essential navigation and text remain available without those services or
JavaScript. An early CSP meta tag restricts scripts and network origins. The
builder hashes the exact theme bootstrap in `templates/site/partials/theme-init.js`;
inline scripts and eval are otherwise blocked. Inline styles remain allowed for
math, diagrams, and table alignment. The analytics origins cover basic GA4;
enabling advertising features requires reviewing the policy in `builder/config.py`.
GitHub Pages controls HTTP response headers, so the meta policy cannot configure
server-only controls such as frame-ancestors or HSTS.

## Design notes

Interactive features target current browsers with native modules, MathML,
`matchMedia`, and the Font Loading API. Mermaid uses native MathML for diagram
equations; no separate KaTeX stylesheet is loaded. The native mode follows
[Mermaid's current math configuration](https://mermaid.js.org/config/math.html).

- Shared styling lives in `static/css/site.css`; `static/css/blog.css` loads
  only for blog pages. Local styles, scripts, and the favicon use content hashes
  in their URLs so cached assets update after publishing. Light and dark themes
  share semantic tokens. Prose,
  publication rows, and light separators establish the editorial layout.
- JavaScript is dependency-free and page-scoped: `static/js/site.js` (theme,
  nav, scrollspy, analytics) plus page enhancements for paper filtering, blog
  navigation, copying, and optional renderers. MathJax loading and typesetting
  are shared and retryable; the homepage loads it only for an opened math abstract.
- Table scroll wrappers and code labels are generated during the Markdown build;
  the browser adds keyboard focus only when a region actually overflows. Diagram
  palettes use `tone1`–`tone5`, `neutral`, and `accent` classes in `blog.css`.
- Theme preference is stored in `wy-theme` and `wy-theme-source`; without a
  saved manual choice, the site follows the system theme.
