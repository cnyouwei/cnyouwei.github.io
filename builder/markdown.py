"""Markdown rendering for blog posts: front matter, math-safe conversion, TOC."""

from __future__ import annotations

import datetime as dt
from html.parser import HTMLParser
import re
from pathlib import Path
from typing import Any

from .validation import DataError, slug_value, text_value, validate_authored_html

try:
    import markdown as markdown_lib
    import pymdownx.superfences as superfences
except ImportError as exc:  # pragma: no cover - required dependency
    raise RuntimeError(
        "Missing markdown dependencies. Install with: python3 -m pip install -r requirements.txt"
    ) from exc

EXTENSIONS = ["tables", "toc", "pymdownx.tasklist", "pymdownx.superfences", "pymdownx.arithmatex"]
EXTENSION_CONFIGS: dict[str, dict[str, Any]] = {
    "toc": {"permalink": False},
    "pymdownx.tasklist": {"custom_checkbox": True},
    "pymdownx.arithmatex": {"generic": True},
    "pymdownx.superfences": {
        # Keep Mermaid fences as dedicated blocks consumed by the blog runtime.
        "custom_fences": [
            {"name": "mermaid", "class": "mermaid", "format": superfences.fence_code_format}
        ]
    },
}


def parse_front_matter(raw: str) -> tuple[dict[str, str], str]:
    """Split a leading `--- ... ---` block into a flat key: value dict + body."""
    raw = raw.replace("\r\n", "\n")
    if not raw.endswith("\n"):
        raw += "\n"  # Match the closing delimiter even at EOF.
    if not raw.startswith("---\n"):
        raise DataError("blog front matter: expected an opening ---")
    end = raw.find("\n---\n", 4)
    if end == -1:
        raise DataError("blog front matter: missing closing ---")
    meta: dict[str, str] = {}
    for line in raw[4:end].splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            raise DataError(f"blog front matter: expected key: value, got {stripped!r}")
        key, value = stripped.split(":", 1)
        if key.strip() in meta:
            raise DataError(f"blog front matter: duplicate key '{key.strip()}'")
        meta[key.strip()] = value.strip().strip("\"'")
    if not meta:
        raise DataError("blog front matter: metadata block is empty")
    return meta, raw[end + 5 :].strip()


def parse_tags(raw_tags: str) -> list[str]:
    text = raw_tags.strip()
    if text.startswith("[") and text.endswith("]"):
        text = text[1:-1]
    return [t.strip().strip("\"'") for t in text.split(",") if t.strip().strip("\"'")]


def _heading_text(rendered: str) -> str:
    """Extract visible heading text without mistaking escaped math for HTML."""
    parts: list[str] = []

    class HeadingText(HTMLParser):
        def handle_data(self, value):
            parts.append(value)

    parser = HeadingText(convert_charrefs=True)
    parser.feed(rendered)
    parser.close()
    return re.sub(r"\s+", " ", "".join(parts).replace("\\", "")).strip()


def _flatten_toc(tokens: list[dict[str, Any]], out: list[dict[str, Any]]) -> None:
    for token in tokens:
        token_id = token["id"]
        title = _heading_text(token["name"])
        if token_id and title and title.lower() != "table of contents":
            out.append({"id": token_id, "title": title, "level": token["level"]})
        _flatten_toc(token["children"], out)


def to_html(markdown_source: str) -> tuple[str, list[dict[str, Any]]]:
    """Render markdown to HTML. Returns (body_html, toc_entries)."""
    md = markdown_lib.Markdown(
        extensions=EXTENSIONS, extension_configs=EXTENSION_CONFIGS, output_format="html5"
    )
    body = md.convert(markdown_source)
    # Keep diagram source in a plain pre; the runtime passes its text to Mermaid.
    body = re.sub(
        r'<pre class="mermaid"><code>(.+?)</code></pre>',
        lambda m: f'<pre class="mermaid">{m.group(1)}</pre>',
        body,
        flags=re.DOTALL,
    )
    toc: list[dict[str, Any]] = []
    _flatten_toc(md.toc_tokens, toc)
    validate_authored_html(body)
    return body, toc


def _normalize_date(value: str) -> str:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise DataError("blog date: supply YYYY-MM-DD in front matter")
    try:
        return dt.date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise DataError(f"blog date: invalid calendar date '{value}'") from exc


def format_date(date_string: str) -> str:
    return dt.date.fromisoformat(date_string).strftime("%B %d, %Y")


def load_post(source: Path) -> dict[str, Any]:
    """Read one data/blog/*.md file into a fully rendered post dict."""
    raw = source.read_text(encoding="utf-8")
    try:
        meta, body = parse_front_matter(raw)
        slug = slug_value(meta.get("slug", source.stem), "blog slug")
        title = text_value(meta.get("title"), "blog title")
        date = _normalize_date(text_value(meta.get("date"), "blog date"))
        summary = text_value(meta.get("summary"), "blog summary")
        body_html, toc = to_html(body)
    except DataError as exc:
        raise DataError(f"{source.name}: {exc}") from exc
    return {
        "slug": slug,
        "title": title,
        "date": date,
        "date_label": format_date(date),
        "summary": summary,
        "tags": parse_tags(meta.get("tags", "")),
        "eyebrow": meta.get("eyebrow", "").strip() or "Research Notes",
        "body_html": body_html,
        "toc": toc,
    }
