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

EXTENSIONS = ["tables", "toc", "pymdownx.tasklist", "pymdownx.highlight", "pymdownx.superfences", "pymdownx.arithmatex"]
EXTENSION_CONFIGS: dict[str, dict[str, Any]] = {
    "toc": {"permalink": False},
    "pymdownx.tasklist": {"custom_checkbox": True},
    # Always leave code highlighting to the browser, even if Pygments is installed.
    "pymdownx.highlight": {"use_pygments": False},
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


def _label_wide_content(body: str) -> str:
    """Add scroll containers/labels without reserializing authored HTML or math."""
    line_starts = [0, *(match.end() for match in re.finditer("\n", body))]
    insertions: dict[int, str] = {}
    void_tags = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    class WideContent(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=False)
            self.stack: list[tuple[str, dict[str, str | None], int, int]] = []
            self.tables: dict[int, str] = {}
            self.table_count = 0
            self.code_count = 0

        def position(self) -> int:
            line, column = self.getpos()
            return line_starts[line - 1] + column

        def label(self, attrs: dict[str, str | None], end: int, label: str) -> None:
            if "data-scroll-label" not in attrs:
                insertions[end - 1] = f' data-scroll-label="{label}"'
                attrs["data-scroll-label"] = label

        def handle_starttag(self, tag, attributes):
            attrs = dict(attributes)
            start = self.position()
            end = start + len(self.get_starttag_text())
            if tag == "pre" and "mermaid" not in (attrs.get("class") or "").split():
                self.code_count += 1
                self.label(attrs, end, f"Code example {self.code_count}: scroll horizontally to explore")
            elif tag == "table":
                self.table_count += 1
                label = f"Table {self.table_count}: scroll horizontally to explore"
                parent = self.stack[-1] if self.stack else None
                if parent and parent[0] == "div" and "table-scroll" in (parent[1].get("class") or "").split():
                    self.label(parent[1], parent[3], label)
                else:
                    self.tables[start] = label
            if tag not in void_tags:
                self.stack.append((tag, attrs, start, end))

        def handle_endtag(self, tag):
            for index in range(len(self.stack) - 1, -1, -1):
                if self.stack[index][0] != tag:
                    continue
                start = self.stack[index][2]
                if tag == "table" and start in self.tables:
                    # Wait for the closing tag so incomplete authored tables are
                    # left untouched. Nested tables get independent wrappers.
                    insertions[start] = insertions.get(start, "") + f'<div class="table-scroll" data-scroll-label="{self.tables[start]}">'
                    end = body.index(">", self.position()) + 1
                    insertions[end] = insertions.get(end, "") + "</div>"
                del self.stack[index:]
                break

        def handle_startendtag(self, tag, attributes):
            pass  # Preserve self-closing authored markup exactly.

    parser = WideContent()
    parser.feed(body)
    parser.close()
    for position, insertion in sorted(insertions.items(), reverse=True):
        body = body[:position] + insertion + body[position:]
    return body


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
    body = _label_wide_content(body)
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
    date = dt.date.fromisoformat(date_string)
    return f"{date:%B} {date.day}, {date.year}"


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
