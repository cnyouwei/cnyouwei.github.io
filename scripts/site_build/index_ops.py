from __future__ import annotations

import re

from .common import INDEX_PATH, indent_block

def update_index_block(start_marker: str, end_marker: str, markup: str) -> None:
    html_text = INDEX_PATH.read_text(encoding="utf-8")

    pattern = re.compile(
        rf"^(?P<indent>[ \t]*){re.escape(start_marker)}\n(?P<body>.*?)(?P=indent){re.escape(end_marker)}",
        re.DOTALL | re.MULTILINE,
    )
    match = pattern.search(html_text)
    if not match:
        raise ValueError(f"Markers {start_marker} / {end_marker} were not found in index.html")

    indent = match.group("indent")
    replacement = (
        f"{indent}{start_marker}\n"
        f"{indent_block(markup, indent)}\n"
        f"{indent}{end_marker}"
    )

    updated_html = html_text[: match.start()] + replacement + html_text[match.end() :]
    INDEX_PATH.write_text(updated_html, encoding="utf-8")

