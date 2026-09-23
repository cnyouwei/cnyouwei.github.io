"""Render the website into dist/."""

from __future__ import annotations

import base64
import shutil
import datetime as dt
from dataclasses import dataclass, field
import hashlib
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlsplit
from xml.etree import ElementTree

from markupsafe import Markup

from .config import (
    ASSETS_DIR,
    BADGE_LABELS,
    CONTENT_SECURITY_POLICY,
    CV_PDF,
    DIST_DIR,
    STATIC_DIR,
    PAPER_TYPES,
    RUNTIME_URLS,
    SITE_TEMPLATES_DIR,
    VENUE_TIER_LABELS,
    ga_id,
    paper_citation,
    venue_metadata,
    venue_tier as classify_venue_tier,
)
from .data import SiteData
from .render import author_list, site_env
from .validation import DataError, local_target, slug_value


def _prepare_paper(paper: dict[str, Any], highlight: list[str]) -> dict[str, Any]:
    venue_name = paper.get("venue")
    venue = venue_metadata(venue_name) if venue_name else None
    venue_tier = classify_venue_tier(venue_name) if venue_name else None
    search_blob = " ".join(
        [
            paper["title"],
            " ".join(paper["authors"]),
            venue_name or "",
            paper.get("venue_display") or "",
            venue.abbreviation if venue else "",
            paper.get("status", ""),
            paper.get("topic", ""),
            str(paper["year"]),
        ]
    ).lower()
    return {
        **paper,
        "authors_html": author_list(paper["authors"], highlight),
        "citation": paper_citation(paper),
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

    # Inline exactly the normalized text whose hash is allowed by the policy.
    theme_js = (SITE_TEMPLATES_DIR / "partials" / "theme-init.js").read_text(encoding="utf-8").strip()
    theme_hash = "sha256-" + base64.b64encode(hashlib.sha256(theme_js.encode("utf-8")).digest()).decode("ascii")

    students = data.team["students"]
    measurement_id = ga_id(data.profile["site"]["ga_id"])
    site_url = data.profile["site"]["base_url"]
    profile = data.profile
    share_image_url = urljoin(f"{site_url}/", profile["avatar"].get("share_src", profile["avatar"]["src"]))
    person_json = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": profile["name"],
        **({"alternateName": profile["name_cn"]} if profile.get("name_cn") else {}),
        "jobTitle": profile["position"][0],
        "affiliation": {"@type": "CollegeOrUniversity", "name": profile["position"][-1]},
        "url": f"{site_url}/",
        "image": share_image_url,
        "sameAs": [link["url"] for link in profile["links"] if urlsplit(link["url"]).scheme == "https"],
    }
    return {
        "profile": data.profile,
        "site_url": site_url,
        "share_image_url": share_image_url,
        "person_json": person_json,
        "build_year": dt.datetime.now(dt.timezone.utc).year,
        "paper_types": PAPER_TYPES,
        "asset_versions": static_asset_versions(STATIC_DIR),
        "runtime_config": {**RUNTIME_URLS, "ga_id": measurement_id, "production_hostname": urlsplit(site_url).hostname},
        "badge_labels": BADGE_LABELS,
        "theme_init_js": Markup(theme_js),
        "content_security_policy": CONTENT_SECURITY_POLICY.format(theme_hash=theme_hash),
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


def static_asset_versions(source: Path) -> dict[str, str]:
    """Stable cache keys change only when the deployed asset bytes change."""
    return {
        path.relative_to(source).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()[:12]
        for path in source.rglob("*")
        if path.is_file() and path.name != ".DS_Store" and "__pycache__" not in path.parts
    }


@dataclass(frozen=True)
class Page:
    """One rendered URL; the same registry drives metadata and the sitemap."""

    path: str
    template: str
    title: str
    description: str
    page_id: str
    root: str = ""
    scripts: tuple[str, ...] = ()
    values: dict[str, Any] = field(default_factory=dict)
    indexed: bool = True


def page_registry(data: SiteData) -> list[Page]:
    profile = data.profile["site"]
    pages = [Page(
        path="index.html", template="home.html.j2", title=profile["title"],
        description=profile["meta_description"], page_id="home",
        scripts=("pages/research.js",),
    )]
    for post in data.posts:
        slug_value(post["slug"], "blog slug")
        pages.append(Page(
            path=f"blogs/{post['slug']}.html", template="blog_post.html.j2",
            title=f"{post['title']} | {profile['title']}", description=post["summary"],
            page_id="blog-post", root="../",
            scripts=("pages/blog_post.js",), values={"post": post},
        ))
    for course in data.teaching["courses"]:
        slug_value(course["slug"], "course slug")
        if course["published"]:
            pages.append(Page(
                path=f"teaching/{course['slug']}.html", template="course.html.j2",
                title=f"{course['code']} {course['title']} | Teaching", description=course["summary"],
                page_id="course", root="../", values={"course": course},
            ))
    pages.append(Page(
        path="404.html", template="404.html.j2", title=f"Page not found | {profile['title']}",
        description="Find research, teaching materials, and notes on Wei You's website.",
        page_id="not-found", root="/", indexed=False,
    ))
    paths = [page.path.casefold() for page in pages]
    if len(paths) != len(set(paths)):
        raise DataError("duplicate page output path")
    return pages


def _copy_tree(src: Path, dst: Path) -> None:
    for candidate in src.rglob("*"):
        if candidate.is_symlink() and not candidate.resolve().is_relative_to(src.resolve()):
            raise DataError(f"static symlink escapes source directory: {candidate}")
    shutil.copytree(
        src, dst, dirs_exist_ok=True, ignore=shutil.ignore_patterns(".DS_Store", "__pycache__")
    )


def build_site(data: SiteData) -> None:
    env = site_env()
    context = build_context(data)
    pages = page_registry(data)

    # Fresh output directory.
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True)

    # Static files keep their public URLs: css/, js/, assets/, CV.pdf.
    _copy_tree(STATIC_DIR, DIST_DIR)
    _copy_tree(ASSETS_DIR, DIST_DIR / "assets")
    shutil.copy2(CV_PDF, DIST_DIR / "CV.pdf")

    for page in pages:
        page_context = {
            **context, **page.values, "root": page.root, "page_id": page.page_id,
            "page_scripts": page.scripts,
            "page_url": f"{context['site_url']}/{page.path}",
            "page_title": page.title, "page_description": page.description,
            "page_indexed": page.indexed,
        }
        target = local_target(DIST_DIR, page.path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(env.get_template(page.template).render(**page_context), encoding="utf-8")

    sitemap = ElementTree.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for page in pages:
        if page.indexed:
            ElementTree.SubElement(ElementTree.SubElement(sitemap, "url"), "loc").text = f"{context['site_url']}/{page.path}"
    ElementTree.ElementTree(sitemap).write(DIST_DIR / "sitemap.xml", encoding="utf-8", xml_declaration=True)
    (DIST_DIR / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {context['site_url']}/sitemap.xml\n", encoding="utf-8")

    published = sum(1 for c in data.teaching["courses"] if c.get("published"))
    print(
        f"Site built: {len(data.papers)} papers, {len(data.posts)} posts, "
        f"{published} course pages -> {DIST_DIR}"
    )
