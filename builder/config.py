"""Paths and build constants. Everything path-like lives here."""

from __future__ import annotations

from dataclasses import dataclass
import os
import re
from pathlib import Path
from typing import Any

from .validation import DataError

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
GA_ID_PATTERN = r"G-[A-Z0-9]+"


def ga_id(default: str) -> str:
    value = os.environ.get(GA_MEASUREMENT_ID_ENV, default).strip()
    if value and not re.fullmatch(GA_ID_PATTERN, value):
        raise DataError(f"{GA_MEASUREMENT_ID_ENV}: expected an empty string or G- measurement ID")
    return value


# Keep these previously published PDF URLs available for external citations.
# New unlinked PDFs fail the build until deliberately listed here.
PUBLISHED_UNLINKED_PDFS = frozenset({
    "papers/APS2017.pdf",
    "papers/IBM2017.pdf",
    "papers/INFORMS2016.pdf",
    "papers/INFORMS2017.pdf",
    "papers/INFORMS2018.pdf",
    "papers/RQNA_CUHK_SZ.pdf",
    "papers/Whitt_You_RQNA_main.pdf",
    "papers/Whitt_You_flow.pdf",
})

# Paper badge labels by type (site)
BADGE_LABELS = {
    "working": "Working",
    "journal": "Journal",
    "conference": "Conference",
    "thesis": "Thesis",
}
PAPER_TYPES = tuple(BADGE_LABELS)

# Exact runtime versions keep a rebuild from silently changing third-party code.
RUNTIME_URLS = {
    "mathjax_url": "https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-chtml.js",
    "mermaid_url": "https://cdn.jsdelivr.net/npm/mermaid@11.16.1/dist/mermaid.esm.min.mjs",
    "hljs_base_url": "https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.11.1/build/",
}

# Meta CSP works on GitHub Pages; frame-ancestors needs an HTTP header.
# The build hashes the exact theme bootstrap. Inline styles are required by
# Markdown tables and the math/diagram renderers. Analytics permits basic GA4;
# enabling advertising features requires reviewing their additional origins.
CONTENT_SECURITY_POLICY = "; ".join((
    "default-src 'self'",
    "script-src 'self' '{theme_hash}' https://cdn.jsdelivr.net https://www.googletagmanager.com",
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net",
    "font-src 'self' data: https://fonts.gstatic.com https://cdn.jsdelivr.net",
    "img-src 'self' data: https://*.google-analytics.com https://www.googletagmanager.com",
    "connect-src 'self' https://*.google-analytics.com https://*.google.com https://www.googletagmanager.com",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'none'",
))


def paper_citation(paper: dict[str, Any]) -> str:
    """The display citation used by rendering and structural verification."""
    if paper["type"] == "working":
        return paper.get("status", "")
    bits = [paper.get("venue_display") or paper.get("venue")]
    volume, number = paper.get("volume"), paper.get("number")
    if volume:
        bits.append(f"{volume}({number})" if number else volume)
    if paper.get("pages"):
        bits.append(paper["pages"].replace("-", "–"))
    return ", ".join(part for part in bits if part)


@dataclass(frozen=True)
class VenueMetadata:
    """Derived display and ranking metadata for a canonical venue name."""

    abbreviation: str
    memberships: frozenset[str] = frozenset()


# Papers store only the canonical full venue name. Badge abbreviations and
# ranking tiers are inferred here so authors never duplicate them in the data.
# Memberships were checked against the official lists on 2026-07-22; UTD24
# takes precedence when a journal also appears in FT50.
VENUE_METADATA_BY_NAME = {
    "Columbia University": VenueMetadata("Columbia"),
    "Conference on Learning Theory": VenueMetadata("COLT"),
    "INFORMS Journal on Optimization": VenueMetadata("IJOO"),
    "Journal of Machine Learning Research": VenueMetadata("JMLR"),
    "Journal of the American Statistical Association": VenueMetadata("JASA"),
    "Mathematics of Operations Research": VenueMetadata("MOR"),
    "Naval Research Logistics": VenueMetadata("NRL"),
    "Operations Research": VenueMetadata("OR", frozenset({"utd24", "ft50"})),
    "Operations Research Letters": VenueMetadata("ORL"),
    "Production and Operations Management": VenueMetadata(
        "POM", frozenset({"utd24", "ft50"})
    ),
    "Queueing Systems": VenueMetadata("QUESTA"),
    "Stochastic Systems": VenueMetadata("STSY"),
    "Winter Simulation Conference": VenueMetadata("WSC"),
}

VENUE_TIER_LABELS = {
    "utd24": "UTD24 journal",
    "ft50": "FT50 journal",
    "other": "Other venue",
}


def venue_tier_from_memberships(memberships: set[str] | frozenset[str]) -> str:
    """Resolve overlapping journal lists using the site's visual precedence."""
    if "utd24" in memberships:
        return "utd24"
    if "ft50" in memberships:
        return "ft50"
    return "other"


def venue_metadata(venue_name: str) -> VenueMetadata:
    """Return metadata inferred from an exact canonical full venue name."""
    try:
        return VENUE_METADATA_BY_NAME[venue_name]
    except KeyError as exc:
        raise ValueError(f"unrecognized venue name '{venue_name}'") from exc


def venue_tier(venue_name: str) -> str:
    return venue_tier_from_memberships(venue_metadata(venue_name).memberships)
