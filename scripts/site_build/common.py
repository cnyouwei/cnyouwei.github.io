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

def indent_block(block: str, indent: str) -> str:
    return "\n".join((indent + line if line else "") for line in block.splitlines())
