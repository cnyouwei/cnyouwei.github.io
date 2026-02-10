# Wei You - Personal Research Website

This repository contains a static personal research website.

## Structure

- `index.html`: Main website (home, research, talks, teaching, team, about, blog preview).
- `css/site.css`: Site styles (single file, organized by tokens/base/layout/components/pages/media).
- `js/site.js`: Thin runtime bootstrap.
- `js/core/*.js`: Shared runtime features (theme, nav, analytics, back-to-top, utils).
- `js/pages/*.js`: Page-scoped features (research controls, blog enhancements).
- `content/research/papers.json`: Source of truth for working papers and publications.
- `content/blog/*.md`: Source markdown files for blog posts.
- `content/teaching/courses.json`: Source of truth for teaching directory and course pages.
- `requirements.txt`: Optional Python build dependencies for simpler markdown/template rendering.
- `scripts/build_site.py`: Public build entrypoint.
- `scripts/site_build/`: Internal build modules.
  - `cli.py`: Build orchestration.
  - `common.py`: Shared constants and utility helpers.
  - `index_ops.py`: Marker block replacement in `index.html`.
  - `nav.py`: Shared nav dropdown rendering and index dropdown updates.
  - `markdown_render.py`: Front matter parsing + markdown rendering (library-first, fallback parser).
  - `blog.py`: Blog manifest generation and blog page rendering.
  - `research.py`: Research section rendering and selected-paper updates.
  - `teaching.py`: Teaching directory and per-course page rendering.
  - `template_engine.py`: Template rendering (Jinja2 if installed, fallback renderer otherwise).
  - `templates.py`: Shared injected snippet helpers (theme bootstrap, MathJax config, fonts).
- `scripts/templates/`: HTML templates and partials used by the generator.
- `scripts/parity_check.py`: Snapshot/check utility for generated-output parity.
- `blogs/`: Generated blog output (`index.html`, post pages, `posts.json`, and `posts.js`).
- `teaching/`: Generated teaching output (`index.html` and per-course pages).

## Build

Optional dependency install (recommended for simpler markdown/template pipeline):

```bash
python3 -m pip install -r requirements.txt
```

Build from repository root:

```bash
python3 scripts/build_site.py
```

This updates:

- Blog outputs in `blogs/`
- Teaching outputs in `teaching/`
- Marker blocks in `index.html`

Build command contract is unchanged:

```bash
python3 scripts/build_site.py
```

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
- Marker block contents in `index.html` for:
  - `SELECTED-PAPERS`
  - `RESEARCH-CONTENT`
  - `NAV-TEACHING-DROPDOWN`
  - `NAV-BLOG-DROPDOWN`

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
summary: One-sentence summary shown on the blog index and homepage.
tags: [queueing, teaching]
---

Write your post in markdown here.
```

`eyebrow` is optional; if omitted, blog post pages use `Research Notes`.

3. Build site pages:

```bash
python3 scripts/build_site.py
```

4. Commit both the markdown source and generated files under `blogs/`.

## Add or Update Course Pages

1. Edit `content/teaching/courses.json`.
2. For each course, set:
   - `published: true` to generate a course page at `teaching/<slug>.html`
   - `published: false` to show it as "Coming Soon" in the teaching directory
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
  - `js/core/*.js`
  - `js/pages/*.js`
  - `js/site.js`
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
