"""Jinja2 environment and filters for the HTML site templates."""

from __future__ import annotations

import re

from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup, escape

from . import markdown as md
from .config import SITE_TEMPLATES_DIR

_INLINE_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")


def md_links(text: str) -> Markup:
    """Render a plain string allowing only inline [label](url) markdown links.

    Used for bio paragraphs so data/profile.json stays readable.
    External links open in a new tab.
    """
    parts: list[str] = []
    pos = 0
    for match in _INLINE_LINK.finditer(text):
        parts.append(str(escape(text[pos : match.start()])))
        label, url = escape(match.group(1)), escape(match.group(2))
        external = str(url).startswith(("http://", "https://"))
        target = ' target="_blank" rel="noopener noreferrer"' if external else ""
        parts.append(f'<a href="{url}"{target}>{label}</a>')
        pos = match.end()
    parts.append(str(escape(text[pos:])))
    return Markup("".join(parts))


def author_list(authors: list[str], highlight: list[str]) -> Markup:
    """'A, B, and C' with highlighted (own) names wrapped in a span."""
    rendered = [
        f'<span class="author-me">{escape(a)}</span>' if a in highlight else str(escape(a))
        for a in authors
    ]
    if len(rendered) == 1:
        joined = rendered[0]
    elif len(rendered) == 2:
        joined = f"{rendered[0]} and {rendered[1]}"
    else:
        joined = ", ".join(rendered[:-1]) + f", and {rendered[-1]}"
    return Markup(joined)


def site_env() -> Environment:
    # Default Undefined: optional fields (paper.note, student.placement, ...)
    # simply render nothing; required fields are enforced by builder.data.
    env = Environment(
        loader=FileSystemLoader(SITE_TEMPLATES_DIR),
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["md_links"] = md_links
    env.filters["format_date"] = md.format_date
    return env
