from __future__ import annotations

import datetime as dt
import html
import re

try:
    import markdown as markdown_lib  # type: ignore
except Exception as exc:  # pragma: no cover - required dependency
    raise RuntimeError(
        "Missing markdown dependency `markdown`. "
        "Install build requirements with: python3 -m pip install -r requirements.txt"
    ) from exc

try:
    import pymdownx  # type: ignore # noqa: F401
except Exception as exc:  # pragma: no cover - required dependency
    raise RuntimeError(
        "Missing markdown dependency `pymdown-extensions`. "
        "Install build requirements with: python3 -m pip install -r requirements.txt"
    ) from exc
try:
    import pymdownx.superfences as superfences  # type: ignore
except Exception as exc:  # pragma: no cover - required dependency
    raise RuntimeError(
        "Missing markdown dependency `pymdown-extensions` superfences module. "
        "Install build requirements with: python3 -m pip install -r requirements.txt"
    ) from exc


def parse_front_matter(raw: str) -> tuple[dict[str, str], str]:
    if not raw.startswith("---\n"):
        return {}, raw.strip()

    end_index = raw.find("\n---\n", 4)
    if end_index == -1:
        return {}, raw.strip()

    meta_block = raw[4:end_index]
    body = raw[end_index + 5 :].strip()

    meta: dict[str, str] = {}
    for line in meta_block.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        meta[key.strip()] = value.strip()

    return meta, body


def parse_tags(raw_tags: str) -> list[str]:
    if not raw_tags:
        return []

    text = raw_tags.strip()
    if text.startswith("[") and text.endswith("]"):
        text = text[1:-1]

    tags = []
    for item in text.split(","):
        tag = item.strip().strip('"').strip("'")
        if tag:
            tags.append(tag)
    return tags


def strip_markdown(raw: str, *, collapse_spaces: bool = True) -> str:
    text = html.unescape(raw)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = text.replace("\\", "")
    text = re.sub(r"<[^>]+>", "", text)
    if collapse_spaces:
        text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_date(raw_value: str, fallback: str | None) -> str:
    if raw_value and re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw_value):
        return raw_value
    if fallback and re.fullmatch(r"\d{4}-\d{2}-\d{2}", fallback):
        return fallback
    return dt.date.today().isoformat()


def get_summary(meta_summary: str, markdown_body: str) -> str:
    if meta_summary:
        return meta_summary

    for line in markdown_body.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            cleaned = re.sub(r"[*`_>#-]", "", stripped)
            return cleaned[:180]

    return "New research note."


def _protect_math_segments(text: str) -> tuple[str, list[str]]:
    tokens: list[str] = []

    def stash(match: re.Match[str]) -> str:
        token = f"@@MATHSEG{len(tokens)}@@"
        tokens.append(match.group(0))
        return token

    protected = re.sub(r"\\\[(.+?)\\\]", stash, text, flags=re.DOTALL)
    protected = re.sub(r"\$\$(.+?)\$\$", stash, protected, flags=re.DOTALL)
    protected = re.sub(r"\\\((.+?)\\\)", stash, protected)
    protected = re.sub(r"(?<!\\)\$(?!\$)(.+?)(?<!\\)\$(?!\$)", stash, protected)
    return protected, tokens


def _restore_math_segments(text: str, tokens: list[str]) -> str:
    restored = text
    for idx, segment in enumerate(tokens):
        restored = restored.replace(f"@@MATHSEG{idx}@@", segment)
    return restored


def _flatten_toc_tokens(tokens: list[dict[str, object]], output: list[dict[str, object]]) -> None:
    for token in tokens:
        token_id = str(token.get("id", "")).strip()
        raw_name = str(token.get("name", "")).strip()
        level_value = token.get("level", 2)
        try:
            level = int(level_value)
        except (TypeError, ValueError):
            level = 2
        title = strip_markdown(raw_name)
        if token_id and title and title.lower() != "table of contents":
            output.append({"id": token_id, "title": title, "level": level})
        children = token.get("children", [])
        if isinstance(children, list):
            _flatten_toc_tokens(children, output)


def markdown_to_html(markdown_source: str) -> tuple[str, list[dict[str, object]]]:
    extensions = [
        "fenced_code",
        "tables",
        "toc",
        "pymdownx.tasklist",
        "pymdownx.superfences",
    ]
    extension_configs: dict[str, dict[str, object]] = {
        "toc": {"permalink": False},
        "pymdownx.tasklist": {"custom_checkbox": True},
        "pymdownx.superfences": {
            # Keep Mermaid fences as dedicated blocks consumed by blog runtime.
            "custom_fences": [
                {
                    "name": "mermaid",
                    "class": "mermaid",
                    "format": superfences.fence_code_format,
                }
            ]
        },
    }

    protected_source, math_tokens = _protect_math_segments(markdown_source)
    md = markdown_lib.Markdown(
        extensions=extensions,
        extension_configs=extension_configs,
        output_format="html5",
    )
    body_html = md.convert(protected_source)
    body_html = _restore_math_segments(body_html, math_tokens)

    # Keep existing contract for Mermaid blocks consumed by blog runtime.
    body_html = re.sub(
        r'<pre><code class="language-mermaid">(.+?)</code></pre>',
        lambda match: f'<pre class="mermaid">{match.group(1)}</pre>',
        body_html,
        flags=re.DOTALL,
    )

    toc_entries: list[dict[str, object]] = []
    toc_tokens = getattr(md, "toc_tokens", [])
    if isinstance(toc_tokens, list):
        _flatten_toc_tokens(toc_tokens, toc_entries)

    return body_html, toc_entries
