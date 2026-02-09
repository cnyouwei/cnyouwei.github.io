from __future__ import annotations

import re
from pathlib import Path

from .common import ROOT_DIR

TEMPLATE_DIR = ROOT_DIR / "scripts" / "templates"

try:
    from jinja2 import Environment, FileSystemLoader  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    Environment = None  # type: ignore[assignment]
    FileSystemLoader = None  # type: ignore[assignment]


def _render_fallback(template_name: str, context: dict[str, object]) -> str:
    def load_template(path: str) -> str:
        text = (TEMPLATE_DIR / path).read_text(encoding="utf-8")

        def replace_include(match: re.Match[str]) -> str:
            include_path = match.group("path")
            return load_template(include_path)

        include_pattern = re.compile(
            r"\{%-?\s*include\s+['\"](?P<path>[^'\"]+)['\"]\s*-?%\}"
        )
        text = include_pattern.sub(replace_include, text)
        return text

    rendered = load_template(template_name)

    def replace_var(match: re.Match[str]) -> str:
        key = match.group("key")
        value = context.get(key, "")
        return str(value)

    var_pattern = re.compile(r"\{\{\s*(?P<key>[a-zA-Z0-9_]+)\s*\}\}")
    return var_pattern.sub(replace_var, rendered)


def render_template(template_name: str, context: dict[str, object]) -> str:
    if Environment is not None and FileSystemLoader is not None:
        env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=False)
        template = env.get_template(template_name)
        return template.render(**context)

    return _render_fallback(template_name, context)
