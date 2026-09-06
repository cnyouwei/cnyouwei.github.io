"""Shared data, URL, and path validation for trusted authored site content."""

from __future__ import annotations

from pathlib import Path
from html.parser import HTMLParser
import re
from urllib.parse import unquote, urlsplit


_AUTHORED_HTML_TAGS = frozenset({
    "a", "abbr", "article", "aside", "b", "blockquote", "br", "caption", "code",
    "col", "colgroup", "dd", "del", "details", "div", "dl", "dt", "em", "figcaption",
    "figure", "footer", "h1", "h2", "h3", "h4", "h5", "h6", "header", "hr", "i",
    "img", "input", "kbd", "label", "li", "mark", "ol", "p", "pre", "s", "section", "small",
    "span", "strong", "sub", "summary", "sup", "table", "tbody", "td", "th", "thead",
    "time", "tr", "tfoot", "ul",
})


class DataError(ValueError):
    """An authoring error with enough context to fix the source."""


def object_value(value, where: str) -> dict:
    if not isinstance(value, dict):
        raise DataError(f"{where}: expected an object")
    return value


def list_value(value, where: str) -> list:
    if not isinstance(value, list):
        raise DataError(f"{where}: expected a list")
    return value


def text_value(value, where: str, *, empty: bool = False) -> str:
    if not isinstance(value, str) or (not empty and not value.strip()):
        raise DataError(f"{where}: expected a {'possibly empty' if empty else 'non-empty'} string")
    return value


def slug_value(value, where: str) -> str:
    value = text_value(value, where)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", value):
        raise DataError(f"{where}: use letters, digits, hyphens, and underscores only")
    return value


def local_target(root: Path, path: str, *, relative_to: Path | None = None) -> Path:
    """Resolve a URL path and reject paths/symlinks escaping the output root."""
    decoded = unquote(path)
    if "\\" in decoded or any(ord(c) < 32 for c in decoded):
        raise DataError(f"invalid local path: {path}")
    base = root if decoded.startswith("/") else (relative_to or root)
    target = (base / decoded.lstrip("/")).resolve()
    if not target.is_relative_to(root.resolve()):
        raise DataError(f"local path escapes the site: {path}")
    return target


def url_value(value, where: str):
    """Allow ordinary web/email links and local paths; reject executable URLs."""
    value = text_value(value, where)
    if value != value.strip() or "\\" in value or any(ord(c) < 32 for c in value):
        raise DataError(f"{where}: invalid whitespace or backslash in URL")
    try:
        parsed = urlsplit(value)
        if parsed.scheme not in ("", "http", "https", "mailto"):
            raise ValueError(f"unsupported URL scheme '{parsed.scheme}'")
        if parsed.scheme in ("http", "https"):
            if not parsed.hostname or parsed.username or parsed.password:
                raise ValueError("web URL must have a hostname and no credentials")
            parsed.port  # validate malformed ports
        elif parsed.scheme == "mailto":
            if not parsed.path or "@" not in parsed.path:
                raise ValueError("mailto URL must contain an email address")
        elif parsed.netloc or value.startswith("//"):
            raise ValueError("protocol-relative URLs are not supported; use https://")
    except ValueError as exc:
        raise DataError(f"{where}: {exc}") from exc
    return parsed


def validate_authored_html(source: str) -> None:
    """Allow authored layout HTML, while failing on executable/embedded content."""
    class AuthoredHTML(HTMLParser):
        def handle_starttag(self, tag, attrs):
            if tag not in _AUTHORED_HTML_TAGS:
                raise DataError(f"blog HTML: <{tag}> is not allowed in authored content")
            attributes = dict(attrs)
            if tag == "input" and (attributes.get("type") != "checkbox" or "disabled" not in attributes):
                raise DataError("blog HTML: only disabled task-list checkboxes are allowed")
            for name, value in attrs:
                if name == "style" and tag in {"th", "td"} and value in {
                    "text-align: left;", "text-align: center;", "text-align: right;",
                }:
                    continue  # Alignment emitted by Markdown's tables extension.
                if name.startswith("on") or name in {"srcdoc", "style", "srcset"}:
                    raise DataError(f"blog HTML: '{name}' attributes are not allowed")
                if name in {"href", "src", "poster", "xlink:href"}:
                    url_value(value, f"blog HTML {tag}.{name}")
    parser = AuthoredHTML(convert_charrefs=True)
    parser.feed(source)
    parser.close()
