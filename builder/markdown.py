"""Markdown rendering for blog posts: front matter, math-safe conversion, TOC."""

from __future__ import annotations

import datetime as dt
import html
import re
from pathlib import Path
from typing import Any

try:
    import markdown as markdown_lib
    import pymdownx.superfences as superfences
except ImportError as exc:  # pragma: no cover - required dependency
    raise RuntimeError(
        "Missing markdown dependencies. Install with: python3 -m pip install -r requirements.txt"
    ) from exc

EXTENSIONS = ["fenced_code", "tables", "toc", "pymdownx.tasklist", "pymdownx.superfences"]
EXTENSION_CONFIGS: dict[str, dict[str, Any]] = {
    "toc": {"permalink": False},
    "pymdownx.tasklist": {"custom_checkbox": True},
    "pymdownx.superfences": {
        # Keep Mermaid fences as dedicated blocks consumed by the blog runtime.
        "custom_fences": [
            {"name": "mermaid", "class": "mermaid", "format": superfences.fence_code_format}
        ]
    },
}


def parse_front_matter(raw: str) -> tuple[dict[str, str], str]:
    """Split a leading `--- ... ---` block into a flat key: value dict + body."""
    raw = raw.replace("\r\n", "\n")  # tolerate Windows line endings
    if not raw.endswith("\n"):
        raw += "\n"  # tolerate a closing --- at EOF without trailing newline
    if not raw.startswith("---\n"):
        return {}, raw.strip()
    end = raw.find("\n---\n", 4)
    if end == -1:
        return {}, raw.strip()
    meta: dict[str, str] = {}
    for line in raw[4:end].splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        meta[key.strip()] = value.strip().strip("\"'")
    if not meta:
        return {}, raw.strip()  # the opening --- was a horizontal rule, not front matter
    return meta, raw[end + 5 :].strip()


def parse_tags(raw_tags: str) -> list[str]:
    text = raw_tags.strip()
    if text.startswith("[") and text.endswith("]"):
        text = text[1:-1]
    return [t.strip().strip("\"'") for t in text.split(",") if t.strip().strip("\"'")]


def strip_markdown(raw: str) -> str:
    text = html.unescape(raw)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = text.replace("\\", "")
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _protect_math(text: str) -> tuple[str, list[str]]:
    """Stash $...$ / $$...$$ / \\(...\\) / \\[...\\] so markdown doesn't mangle them."""
    tokens: list[str] = []

    def stash(match: re.Match[str]) -> str:
        tokens.append(match.group(0))
        return f"@@MATHSEG{len(tokens) - 1}@@"

    protected = re.sub(r"\\\[(.+?)\\\]", stash, text, flags=re.DOTALL)
    protected = re.sub(r"\$\$(.+?)\$\$", stash, protected, flags=re.DOTALL)
    protected = re.sub(r"\\\((.+?)\\\)", stash, protected)
    protected = re.sub(r"(?<!\\)\$(?!\$)(.+?)(?<!\\)\$(?!\$)", stash, protected)
    return protected, tokens


def _restore_math(text: str, tokens: list[str]) -> str:
    for idx, segment in enumerate(tokens):
        # Escape <, >, & so math like $x<y$ cannot open a bogus HTML tag.
        # MathJax reads decoded DOM text, so entities are transparent to it.
        text = text.replace(f"@@MATHSEG{idx}@@", html.escape(segment, quote=False))
    return text


def _flatten_toc(tokens: list[dict[str, Any]], out: list[dict[str, Any]]) -> None:
    for token in tokens:
        token_id = str(token.get("id", "")).strip()
        title = strip_markdown(str(token.get("name", "")).strip())
        try:
            level = int(token.get("level", 2))
        except (TypeError, ValueError):
            level = 2
        if token_id and title and title.lower() != "table of contents":
            out.append({"id": token_id, "title": title, "level": level})
        children = token.get("children", [])
        if isinstance(children, list):
            _flatten_toc(children, out)


def to_html(markdown_source: str) -> tuple[str, list[dict[str, Any]]]:
    """Render markdown to HTML. Returns (body_html, toc_entries)."""
    protected, math_tokens = _protect_math(markdown_source)
    md = markdown_lib.Markdown(
        extensions=EXTENSIONS, extension_configs=EXTENSION_CONFIGS, output_format="html5"
    )
    body = md.convert(protected)
    body = _restore_math(body, math_tokens)
    # Superfences emits <pre class="mermaid"><code>...</code></pre>; Mermaid v10
    # reads element.innerHTML, so the inner <code> wrapper must be stripped or
    # it becomes part of the diagram text and the parse fails.
    body = re.sub(
        r'<pre class="mermaid"><code>(.+?)</code></pre>',
        lambda m: f'<pre class="mermaid">{m.group(1)}</pre>',
        body,
        flags=re.DOTALL,
    )
    toc: list[dict[str, Any]] = []
    if isinstance(getattr(md, "toc_tokens", None), list):
        _flatten_toc(md.toc_tokens, toc)
    return body, toc


def _normalize_date(raw: str, fallback: str | None) -> str:
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw or ""):
        return raw
    if fallback and re.fullmatch(r"\d{4}-\d{2}-\d{2}", fallback):
        return fallback
    return dt.date.today().isoformat()


def _summary(meta_summary: str, body: str) -> str:
    if meta_summary:
        return meta_summary
    for line in body.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return re.sub(r"[*`_>#-]", "", stripped)[:180]
    return "New research note."


def format_date(date_string: str) -> str:
    try:
        return dt.date.fromisoformat(date_string).strftime("%B %d, %Y")
    except ValueError:
        return date_string


def load_post(source: Path) -> dict[str, Any]:
    """Read one data/blog/*.md file into a fully rendered post dict."""
    raw = source.read_text(encoding="utf-8")
    meta, body = parse_front_matter(raw)
    date_in_name = re.match(r"^(\d{4}-\d{2}-\d{2})", source.stem)
    body_html, toc = to_html(body)
    date = _normalize_date(meta.get("date", ""), date_in_name.group(1) if date_in_name else None)
    return {
        "slug": meta.get("slug", source.stem).strip(),
        "title": meta.get("title", source.stem.replace("-", " ")).strip(),
        "date": date,
        "date_label": format_date(date),
        "summary": _summary(meta.get("summary", "").strip(), body),
        "tags": parse_tags(meta.get("tags", "")),
        "eyebrow": meta.get("eyebrow", "").strip() or "Research Notes",
        "body_html": body_html,
        "toc": toc,
    }
