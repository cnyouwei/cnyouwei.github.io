# Wei You - Personal Research Website

This repository contains a static personal research website.

## Structure

- `css/site.css`: Site styles (single file, organized by tokens/base/layout/components/pages/media).
- `js/site.js`: Shared runtime for every page — DOM helpers, theme toggle, nav/section routing, analytics, back-to-top. Exposes `SiteUtils` and `SiteTheme` for the page scripts.
- `js/pages/research.js`: Home research filters/search/ordering and lazy MathJax for abstracts.
- `js/pages/blog_post.js`: Blog post enhancements (TOC, copy buttons, highlighting, Mermaid).
- `content/research/papers.json`: Source of truth for working papers and publications.
- `content/blog/*.md`: Source markdown files for blog posts.
- `content/teaching/courses.json`: Source of truth for home teaching hub cards and course pages.
- `requirements.txt`: Required Python build dependencies for markdown/template rendering.
- `scripts/build_site.py`: Public build entrypoint.
- `scripts/site_build/`: Internal build modules.
  - `cli.py`: Build orchestration.
  - `common.py`: Shared constants, helpers, and the `base.html.j2` page context.
  - `home.py`: Home page rendering (`index.html`).
  - `markdown_render.py`: Front matter parsing + markdown rendering (Python markdown library).
  - `blog.py`: Blog page rendering and home recent-post markup generation.
  - `research.py`: Research section and selected-papers markup rendering.
  - `teaching.py`: Teaching markup rendering and per-course page generation.
  - `template_engine.py`: Template rendering (Jinja2).
- `scripts/templates/`: HTML templates and partials. `base.html.j2` is the page shell; `partials/` holds nav, head assets, theme bootstrap, MathJax config, footer, and the content fragments.
- `scripts/parity_check.py`: Snapshot/check utility for generated-output parity.
- `.github/workflows/pages.yml`: Build-and-deploy pipeline for GitHub Pages.
- `blogs/`: Generated blog output (post pages).
- `teaching/`: Generated teaching output (per-course pages only).

## Build

Install required dependencies (recommended in a virtual environment):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Build from repository root:

```bash
python3 scripts/build_site.py
```

This generates:

- Blog outputs in `blogs/`
- Teaching outputs in `teaching/`
- `index.html`
- and does not require committing generated files.

Build command contract is unchanged:

```bash
python3 scripts/build_site.py
```

Default GA configuration:

```bash
# Defaults to G-W043BW5W9F when WY_GA_MEASUREMENT_ID is unset.
python3 scripts/build_site.py
```

Optional override:

```bash
export WY_GA_MEASUREMENT_ID=G-YYYYYYYYYY
python3 scripts/build_site.py
```

## Deployment (GitHub Pages Actions)

Deploys are handled by `.github/workflows/pages.yml`.

- Trigger: push to `master` or `main` (and manual dispatch).
- Workflow builds the site with `python3 scripts/build_site.py`.
- Workflow uploads a Pages artifact from generated outputs and deploys with `actions/deploy-pages`.

## Parity Workflow (High-Confidence Refactor Guard)

1. Capture baseline snapshot:

```bash
python3 scripts/parity_check.py snapshot --output /tmp/site_parity_baseline.json
```

2. Run build:

```bash
python3 scripts/build_site.py
```

3. Verify parity against baseline:

```bash
python3 scripts/parity_check.py check --baseline /tmp/site_parity_baseline.json
```

The checker validates:

- Generated artifact file set and SHA-256 hashes
- Core `index.html` contract hooks (required page/section/script nodes)

## Manage Research Papers

1. Edit `content/research/papers.json`.
2. Each paper entry supports:
   - `authors` (ordered list)
   - `year`
   - `topic` (for `By Topic` grouping in the Research section)
   - `venue`
   - `abstract`
   - `links` (e.g., arXiv, preprint, journal, slides, code)
   - `selected` (optional boolean; if `true`, appears in Home `Selected Papers`)
   - plus classification fields (`section`, `type`) for filtering and grouping
3. Rebuild the site:

```bash
python3 scripts/build_site.py
```

## Add a New Blog Post

1. Create a new markdown file in `content/blog/`, for example:
   - `content/blog/2026-02-10-my-new-note.md`
2. Use this front matter format:

```md
---
title: My New Note
date: 2026-02-10
eyebrow: Research Notes
summary: One-sentence summary shown on the homepage blog section.
tags: [queueing, teaching]
---

Write your post in markdown here.
```

`eyebrow` is optional; if omitted, blog post pages use `Research Notes`.

3. Build site pages:

```bash
python3 scripts/build_site.py
```

## Add or Update Course Pages

1. Edit `content/teaching/courses.json`.
2. For each course, set:
   - `published: true` to generate a course page at `teaching/<slug>.html`
   - `published: false` to show it as "Coming Soon" in the home `#teaching` hub
3. For published courses, you can define:
   - `institution`, `overview`, `audience`, `prerequisites`, `outcomes`
   - `modules` with `code`, `title`, `description`, `link_label`, and `link_url`
4. Rebuild:

```bash
python3 scripts/build_site.py
```

## Safe Edit Zones

- Content-only edits (lowest risk):
  - `content/research/papers.json`
  - `content/blog/*.md`
  - `content/teaching/courses.json`
- Build/template edits (generator behavior):
  - `scripts/site_build/*.py`
  - `scripts/build_site.py`
- Runtime behavior/style edits (frontend behavior):
  - `js/site.js`
  - `js/pages/*.js`
  - `css/site.css`
- Template/layout edits (page shell and generated markup):
  - `scripts/templates/**/*.j2`

When editing build/template or runtime files, use the parity workflow before and after changes.

## Local Preview

Use any static file server from the repository root.

Example with Python:

```bash
python3 -m http.server 8000
```

Then open `http://localhost:8000`.
