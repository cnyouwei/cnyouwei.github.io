# Wei You - Personal Research Website

This repository contains a fully static personal research website.

## Structure

- `index.html`: Main website (home, research, talks, teaching, team, about, blog preview).
- `css/site.css`: Site styles.
- `js/site.js`: Navigation, paper filter/search, and blog preview loader.
- `content/research/papers.json`: Source of truth for working papers and publications.
- `content/blog/*.md`: Source markdown files for blog posts.
- `content/teaching/courses.json`: Source of truth for teaching directory and course pages.
- `scripts/build_site.py`: Compiles research from `content/research/papers.json`, blog from `content/blog/*.md`, and teaching pages from `content/teaching/courses.json`.
- `blogs/`: Generated blog output (`index.html`, post pages, `posts.json`, and `posts.js`).
- `teaching/`: Generated teaching output (`index.html` and per-course pages).

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

## Add or Update Course Pages

1. Edit `content/teaching/courses.json`.
2. For each course, set:
   - `published: true` to generate a course page at `teaching/<slug>.html`
   - `published: false` to show it as "Coming Soon" in the teaching directory
3. For published courses, you can define:
   - `overview`, `audience`, `prerequisites`, `outcomes`
   - `modules` with `code`, `title`, `description`, `link_label`, and `link_url`
4. Rebuild:

```bash
python3 scripts/build_site.py
```

## Local Preview

Use any static file server from the repository root.

Example with Python:

```bash
python3 -m http.server 8000
```

Then open `http://localhost:8000`.
