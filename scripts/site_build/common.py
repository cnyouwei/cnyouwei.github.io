from __future__ import annotations

import datetime as dt
import html
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# Blog paths
BLOG_SOURCE_DIR = ROOT_DIR / "content" / "blog"
BLOG_OUTPUT_DIR = ROOT_DIR / "blogs"

# Research paths
INDEX_PATH = ROOT_DIR / "index.html"
RESEARCH_DATA_PATH = ROOT_DIR / "content" / "research" / "papers.json"

# Teaching paths
TEACHING_DATA_PATH = ROOT_DIR / "content" / "teaching" / "courses.json"
TEACHING_OUTPUT_DIR = ROOT_DIR / "teaching"

GA_ID_PLACEHOLDER = "G-XXXXXXXXXX"
GA_ID_DEFAULT = "G-W043BW5W9F"
GA_MEASUREMENT_ID_ENV = "WY_GA_MEASUREMENT_ID"

BADGE_LABELS = {
    "working": "Working",
    "journal": "Journal",
    "conference": "Conference",
    "thesis": "Thesis",
}

def escape_html(text: str) -> str:
    return html.escape(text, quote=True)

def read_ga_measurement_id() -> str:
    value = os.environ.get(GA_MEASUREMENT_ID_ENV, "").strip()
    return value if value else GA_ID_DEFAULT

def format_date(date_string: str) -> str:
    try:
        date_obj = dt.date.fromisoformat(date_string)
    except ValueError:
        return date_string
    return date_obj.strftime("%B %d, %Y")

def page_context(
    *,
    ga_id: str,
    page_id: str,
    page_title: str,
    meta_description: str,
    main_html: str,
    subpage: bool = False,
    mathjax: str = "none",
    page_scripts: list[str] | tuple[str, ...] = (),
) -> dict[str, object]:
    """Context for base.html.j2.

    `subpage` flips every page-relative path (assets, nav anchors) in the
    template. `mathjax` is one of "none" | "lazy" | "eager" (see the partial).
    `page_scripts` are paths under js/, loaded after site.js.
    """
    return {
        "ga_id": escape_html(ga_id),
        "page_id": escape_html(page_id),
        "page_title": escape_html(page_title),
        "meta_description": escape_html(meta_description),
        "main_html": main_html,
        "subpage": subpage,
        "mathjax": mathjax,
        "page_scripts": list(page_scripts),
    }
