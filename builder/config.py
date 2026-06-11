"""Paths and build constants. Everything path-like lives here."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Sources
DATA_DIR = ROOT / "data"
BLOG_SOURCE_DIR = DATA_DIR / "blog"
TEMPLATES_DIR = ROOT / "templates"
SITE_TEMPLATES_DIR = TEMPLATES_DIR / "site"
STATIC_DIR = ROOT / "static"
ASSETS_DIR = ROOT / "assets"

# Outputs
DIST_DIR = ROOT / "dist"  # the deployable website artifact

# The CV is maintained separately (CV.tex -> CV.pdf at the repo root) and the
# committed PDF is copied into dist/ as a static file.
CV_PDF = ROOT / "CV.pdf"

# Analytics: override with WY_GA_MEASUREMENT_ID, fall back to profile.json site.ga_id
GA_MEASUREMENT_ID_ENV = "WY_GA_MEASUREMENT_ID"


def ga_id(default: str) -> str:
    value = os.environ.get(GA_MEASUREMENT_ID_ENV, "").strip()
    return value or default


PAPER_TYPES = ("working", "journal", "conference", "thesis")

# Paper badge labels by type (site)
BADGE_LABELS = {
    "working": "Working",
    "journal": "Journal",
    "conference": "Conference",
    "thesis": "Thesis",
}
