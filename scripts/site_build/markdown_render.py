from __future__ import annotations

import datetime as dt
import html
import re

from .common import escape_html

try:
    import markdown as markdown_lib  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    markdown_lib = None

try:
    import pymdownx  # type: ignore # noqa: F401
except Exception:  # pragma: no cover - optional dependency
    HAS_PYMDOWN = False
else:
    HAS_PYMDOWN = True

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

def inline_markdown_to_html(raw: str) -> str:
    text = escape_html(raw)
    math_tokens: list[str] = []

    def stash_math(match: re.Match[str]) -> str:
        token = f"@@MATH{len(math_tokens)}@@"
        math_tokens.append(match.group(0))
        return token

    # Protect math segments so markdown regexes do not mutate TeX content.
    text = re.sub(r"\\\((.+?)\\\)", stash_math, text)
    text = re.sub(r"\\\[(.+?)\\\]", stash_math, text)
    text = re.sub(r"(?<!\\)\$(?!\$)(.+?)(?<!\\)\$(?!\$)", stash_math, text)

    # Inline code first.
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)

    for idx, segment in enumerate(math_tokens):
        text = text.replace(f"@@MATH{idx}@@", segment)

    return text

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

def slugify_heading(raw_title: str) -> str:
    cleaned = strip_markdown(raw_title, collapse_spaces=False).lower()
    cleaned = cleaned.replace("_", "-")
    cleaned = re.sub(r"[^\w\s-]", "", cleaned)
    cleaned = re.sub(r"\s", "-", cleaned)
    cleaned = cleaned.strip("-")
    return cleaned or "section"

def _fallback_markdown_to_html(markdown: str) -> tuple[str, list[dict[str, object]]]:
    lines = markdown.replace("\r\n", "\n").split("\n")
    blocks: list[str] = []
    toc_entries: list[dict[str, object]] = []
    heading_ids: dict[str, int] = {}
    i = 0

    def is_horizontal_rule(line: str) -> bool:
        compact = re.sub(r"\s+", "", line.strip())
        return bool(re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", compact))

    def render_display_math(delimiter: str, expression: str) -> str:
        safe_expression = escape_html(expression.strip())
        if delimiter == "$$":
            return f"<div class=\"math-display\">$$\n{safe_expression}\n$$</div>"
        return f"<div class=\"math-display\">\\[\n{safe_expression}\n\\]</div>"

    def parse_single_line_display_math(line: str) -> str | None:
        stripped = line.strip()
        match_dollars = re.fullmatch(r"\$\$(.+)\$\$", stripped)
        if match_dollars:
            return render_display_math("$$", match_dollars.group(1))

        match_brackets = re.fullmatch(r"\\\[(.+)\\\]", stripped)
        if match_brackets:
            return render_display_math(r"\[", match_brackets.group(1))

        return None

    def render_list_item(raw_item: str) -> tuple[str, bool]:
        task_match = re.match(r"^\[( |x|X)\]\s+(.*)$", raw_item)
        if not task_match:
            return f"<li>{inline_markdown_to_html(raw_item)}</li>", False

        checked = task_match.group(1).lower() == "x"
        checked_attr = " checked" if checked else ""
        item_content = inline_markdown_to_html(task_match.group(2).strip())
        return (
            (
                '<li class="task-list-item">'
                '<label class="task-list-label">'
                f'<input class="task-list-checkbox" type="checkbox"{checked_attr} />'
                f"<span>{item_content}</span>"
                "</label>"
                "</li>"
            ),
            True,
        )

    def collect_paragraph(start: int) -> tuple[str, int]:
        paragraph_lines = []
        j = start

        while j < len(lines):
            line = lines[j]
            stripped = line.strip()
            if not line.strip():
                break
            if re.match(r"^(#{1,6})\s+", line):
                break
            if line.startswith("```"):
                break
            if re.match(r"^[-*]\s+", line):
                break
            if re.match(r"^\d+\.\s+", line):
                break
            if re.match(r"^>\s?", line):
                break
            if is_horizontal_rule(line):
                break
            if stripped in (r"\[", "$$"):
                break
            if parse_single_line_display_math(line):
                break
            paragraph_lines.append(line.strip())
            j += 1

        return " ".join(paragraph_lines), j

    while i < len(lines):
        line = lines[i]

        if not line.strip():
            i += 1
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading_match:
            level = len(heading_match.group(1))
            raw_title = heading_match.group(2).strip()
            heading_text = strip_markdown(raw_title)
            title = inline_markdown_to_html(raw_title)
            base_id = slugify_heading(raw_title)
            count = heading_ids.get(base_id, 0)
            heading_ids[base_id] = count + 1
            heading_id = base_id if count == 0 else f"{base_id}-{count}"
            blocks.append(f'<h{level} id="{escape_html(heading_id)}">{title}</h{level}>')
            if (
                heading_text
                and level in (2, 3)
                and heading_text.strip().lower() != "table of contents"
            ):
                toc_entries.append({"id": heading_id, "title": heading_text, "level": level})
            i += 1
            continue

        if is_horizontal_rule(line):
            blocks.append("<hr />")
            i += 1
            continue

        single_line_math = parse_single_line_display_math(line)
        if single_line_math:
            blocks.append(single_line_math)
            i += 1
            continue

        stripped = line.strip()
        if stripped in (r"\[", "$$"):
            delimiter = stripped
            closing = r"\]" if delimiter == r"\[" else "$$"
            math_lines = []
            i += 1
            while i < len(lines) and lines[i].strip() != closing:
                math_lines.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1
            blocks.append(render_display_math(delimiter, "\n".join(math_lines)))
            continue

        if line.startswith("```"):
            fence_tokens = line[3:].strip().split()
            fence_language = fence_tokens[0].lower() if fence_tokens else ""
            safe_language = re.sub(r"[^a-z0-9_-]+", "", fence_language)
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code_lines.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1
            code_text = escape_html("\n".join(code_lines))
            if safe_language == "mermaid":
                blocks.append(f'<pre class="mermaid">{code_text}</pre>')
            elif safe_language:
                blocks.append(
                    f'<pre><code class="language-{safe_language}">{code_text}</code></pre>'
                )
            else:
                blocks.append(f"<pre><code>{code_text}</code></pre>")
            continue

        if re.match(r"^[-*]\s+", line):
            items = []
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i]):
                items.append(re.sub(r"^[-*]\s+", "", lines[i]).strip())
                i += 1
            rendered_items = []
            has_task_items = False
            for item in items:
                item_markup, is_task = render_list_item(item)
                rendered_items.append(item_markup)
                has_task_items = has_task_items or is_task
            class_attr = ' class="task-list"' if has_task_items else ""
            li = "".join(rendered_items)
            blocks.append(f"<ul{class_attr}>{li}</ul>")
            continue

        if re.match(r"^\d+\.\s+", line):
            items = []
            list_start = 1
            while i < len(lines):
                current = lines[i]
                if not current.strip():
                    # Keep ordered lists contiguous when authors place blank lines between items.
                    j = i
                    while j < len(lines) and not lines[j].strip():
                        j += 1
                    if j < len(lines) and re.match(r"^\d+\.\s+", lines[j]) and items:
                        i = j
                        continue
                    i = j
                    break

                item_match = re.match(r"^(\d+)\.\s+(.*)$", current)
                if not item_match:
                    break

                if not items:
                    list_start = int(item_match.group(1))

                item_text = item_match.group(2).strip()
                i += 1

                # Support indented continuation lines for the same ordered-list item.
                continuation = []
                while i < len(lines):
                    cont_line = lines[i]
                    if not cont_line.strip():
                        break
                    if re.match(r"^\s{2,}\S", cont_line) or cont_line.startswith("\t"):
                        continuation.append(cont_line.strip())
                        i += 1
                        continue
                    break

                if continuation:
                    item_text = item_text + " " + " ".join(continuation)

                items.append(item_text)

            rendered_items = []
            has_task_items = False
            for item in items:
                item_markup, is_task = render_list_item(item)
                rendered_items.append(item_markup)
                has_task_items = has_task_items or is_task
            attrs = ""
            if list_start != 1:
                attrs += f' start="{list_start}"'
            if has_task_items:
                attrs += ' class="task-list"'
            li = "".join(rendered_items)
            blocks.append(f"<ol{attrs}>{li}</ol>")
            continue

        if re.match(r"^>\s?", line):
            quote_lines = []
            while i < len(lines) and re.match(r"^>\s?", lines[i]):
                quote_lines.append(re.sub(r"^>\s?", "", lines[i]).strip())
                i += 1
            quote_text = inline_markdown_to_html(" ".join(quote_lines))
            blocks.append(f"<blockquote>{quote_text}</blockquote>")
            continue

        paragraph, next_index = collect_paragraph(i)
        if paragraph:
            blocks.append(f"<p>{inline_markdown_to_html(paragraph)}</p>")
        i = next_index

    return "\n".join(blocks), toc_entries

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


def _render_with_markdown_library(markdown_source: str) -> tuple[str, list[dict[str, object]]] | None:
    if markdown_lib is None:
        return None

    extensions: list[str] = ["fenced_code", "tables", "toc"]
    if HAS_PYMDOWN:
        extensions.extend(["pymdownx.tasklist", "pymdownx.superfences"])

    extension_configs: dict[str, dict[str, object]] = {"toc": {"permalink": False}}
    if HAS_PYMDOWN:
        extension_configs["pymdownx.tasklist"] = {"custom_checkbox": True}

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


def markdown_to_html(markdown_source: str) -> tuple[str, list[dict[str, object]]]:
    rendered = _render_with_markdown_library(markdown_source)
    if rendered is not None:
        return rendered
    return _fallback_markdown_to_html(markdown_source)
