# Wei You - Personal Research Website

This repository contains a fully static personal research website.

## Structure

- `index.html`: Main website (home, research, talks, teaching, team, about, blog preview).
- `css/site.css`: Site styles.
- `js/site.js`: Navigation, paper filter/search, and blog preview loader.
- `content/research/papers.json`: Source of truth for working papers and publications.
- `content/blog/*.md`: Source markdown files for blog posts.
- `scripts/build_site.py`: Compiles the Research section from `content/research/papers.json` and generates blog pages from `content/blog/*.md`.
- `blogs/`: Generated blog output (`index.html`, post pages, `posts.json`, and `posts.js`).

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

The script updates only the marker block in `index.html` between:
- `<!-- RESEARCH-CONTENT:START -->`
- `<!-- RESEARCH-CONTENT:END -->`

## Add a New Blog Post

1. Create a new markdown file in `content/blog/`, for example:
   - `content/blog/2026-02-10-my-new-note.md`
2. Use this front matter format:

```md
---
title: My New Note
date: 2026-02-10
summary: One-sentence summary shown on the blog index and homepage.
tags: [queueing, teaching]
---

Write your post in markdown here.
```

3. Build site pages:

```bash
python3 scripts/build_site.py
```

4. Commit both the markdown source and generated files under `blogs/`.

## Local Preview

Use any static file server from the repository root.

Example with Python:

```bash
python3 -m http.server 8000
```

Then open `http://localhost:8000`.
