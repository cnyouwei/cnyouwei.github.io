"""Render the website into dist/."""

from __future__ import annotations

import shutil
from typing import Any

from .config import (
    ASSETS_DIR,
    BADGE_LABELS,
    CV_PDF,
    DIST_DIR,
    STATIC_DIR,
    VENUE_TIER_LABELS,
    ga_id,
    venue_metadata,
    venue_tier as classify_venue_tier,
)
from .data import SiteData
from .render import author_list, site_env


def _display_citation(paper: dict[str, Any]) -> str:
    """Venue line shown under a paper title on the site."""
    if paper["type"] == "working":
        return paper.get("status", "")
    bits = [paper.get("venue_display", paper.get("venue", ""))]
    volume = paper.get("volume")
    if volume:
        number = paper.get("number")
        bits.append(f"{volume}({number})" if number else volume)
    if paper.get("pages"):
        bits.append(paper["pages"].replace("-", "–"))
    return ", ".join(b for b in bits if b)


def _prepare_paper(paper: dict[str, Any], highlight: list[str]) -> dict[str, Any]:
    venue_name = paper.get("venue")
    venue = venue_metadata(venue_name) if venue_name else None
    venue_tier = classify_venue_tier(venue_name) if venue_name else None
    search_blob = " ".join(
        [
            paper["title"],
            " ".join(paper["authors"]),
            venue_name or "",
            paper.get("venue_display", ""),
            venue.abbreviation if venue else "",
            paper.get("status", ""),
            paper.get("topic", ""),
            str(paper["year"]),
        ]
    ).lower()
    return {
        **paper,
        "authors_html": author_list(paper["authors"], highlight),
        "citation": _display_citation(paper),
        "search_blob": search_blob,
        "topic": paper.get("topic", "Other"),
        "venue_abbrev": venue.abbreviation if venue else None,
        "venue_tier": venue_tier,
        "venue_tier_label": VENUE_TIER_LABELS[venue_tier] if venue_tier else None,
    }


def build_context(data: SiteData) -> dict[str, Any]:
    papers = [_prepare_paper(p, data.highlight_authors) for p in data.papers]
    by_year = sorted(papers, key=lambda p: p["year"], reverse=True)
    working = [p for p in by_year if p["type"] == "working"]
    publications = [p for p in by_year if p["type"] != "working"]
    selected = [p for p in by_year if p.get("selected")]
    topics = sorted({p["topic"] for p in papers})

    students = data.team["students"]
    return {
        "profile": data.profile,
        "ga_id": ga_id(data.profile["site"]["ga_id"]),
        "badge_labels": BADGE_LABELS,
        "selected_papers": selected,
        "working_papers": working,
        "publications": publications,
        "topics": topics,
        "talks": data.talks,
        "courses": data.teaching["courses"],
        "students_current": [s for s in students if s["status"] == "current"],
        "students_former": [s for s in students if s["status"] == "former"],
        "posts": data.posts,
    }


# Per-page shell settings consumed by base.html.j2.
_HOME_PAGE = {"root": "", "page_id": "home", "mathjax": "lazy", "page_scripts": ["pages/research.js"]}
_BLOG_PAGE = {"root": "../", "page_id": "blog-post", "mathjax": "eager", "page_scripts": ["pages/blog_post.js"]}
_COURSE_PAGE = {"root": "../", "page_id": "course", "mathjax": "none", "page_scripts": []}


def _copy_tree(src, dst) -> None:
    shutil.copytree(
        src, dst, dirs_exist_ok=True, ignore=shutil.ignore_patterns(".DS_Store", "__pycache__")
    )


def build_site(data: SiteData) -> None:
    env = site_env()
    context = build_context(data)

    # Fresh output directory.
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True)

    # Static files keep their public URLs: css/, js/, assets/, CV.pdf.
    _copy_tree(STATIC_DIR, DIST_DIR)
    _copy_tree(ASSETS_DIR, DIST_DIR / "assets")
    if CV_PDF.exists():
        shutil.copy2(CV_PDF, DIST_DIR / "CV.pdf")

    # Home page.
    home = env.get_template("home.html.j2")
    (DIST_DIR / "index.html").write_text(home.render(**context, **_HOME_PAGE), encoding="utf-8")

    # Blog post pages.
    post_template = env.get_template("blog_post.html.j2")
    blog_dir = DIST_DIR / "blogs"
    blog_dir.mkdir()
    for post in data.posts:
        page = post_template.render(post=post, **context, **_BLOG_PAGE)
        (blog_dir / f"{post['slug']}.html").write_text(page, encoding="utf-8")

    # Course pages.
    course_template = env.get_template("course.html.j2")
    teaching_dir = DIST_DIR / "teaching"
    teaching_dir.mkdir()
    for course in data.teaching["courses"]:
        if not course.get("published"):
            continue
        page = course_template.render(course=course, **context, **_COURSE_PAGE)
        (teaching_dir / f"{course['slug']}.html").write_text(page, encoding="utf-8")

    published = sum(1 for c in data.teaching["courses"] if c.get("published"))
    print(
        f"Site built: {len(data.papers)} papers, {len(data.posts)} posts, "
        f"{published} course pages -> {DIST_DIR}"
    )
