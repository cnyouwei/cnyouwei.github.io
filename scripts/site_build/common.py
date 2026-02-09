from __future__ import annotations

import datetime as dt
import html
import re
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

SELECTED_START_MARKER = "<!-- SELECTED-PAPERS:START -->"
SELECTED_END_MARKER = "<!-- SELECTED-PAPERS:END -->"
RESEARCH_START_MARKER = "<!-- RESEARCH-CONTENT:START -->"
RESEARCH_END_MARKER = "<!-- RESEARCH-CONTENT:END -->"
NAV_TEACHING_START_MARKER = "<!-- NAV-TEACHING-DROPDOWN:START -->"
NAV_TEACHING_END_MARKER = "<!-- NAV-TEACHING-DROPDOWN:END -->"
NAV_BLOG_START_MARKER = "<!-- NAV-BLOG-DROPDOWN:START -->"
NAV_BLOG_END_MARKER = "<!-- NAV-BLOG-DROPDOWN:END -->"
GA_ID_PLACEHOLDER = "G-XXXXXXXXXX"

BADGE_LABELS = {
    "working": "Working",
    "journal": "Journal",
    "conference": "Conference",
    "thesis": "Thesis",
}

def escape_html(text: str) -> str:
    return html.escape(text, quote=True)

def read_ga_measurement_id() -> str:
    if not INDEX_PATH.exists():
        return GA_ID_PLACEHOLDER

    index_html = INDEX_PATH.read_text(encoding="utf-8")
    match = re.search(r'<html\b[^>]*\bdata-ga-id="([^"]+)"', index_html, flags=re.IGNORECASE)
    if not match:
        return GA_ID_PLACEHOLDER

    value = match.group(1).strip()
    return value if value else GA_ID_PLACEHOLDER

def format_date(date_string: str) -> str:
    try:
        date_obj = dt.date.fromisoformat(date_string)
    except ValueError:
        return date_string
    return date_obj.strftime("%B %d, %Y")

def indent_block(block: str, indent: str) -> str:
    return "\n".join((indent + line if line else "") for line in block.splitlines())

