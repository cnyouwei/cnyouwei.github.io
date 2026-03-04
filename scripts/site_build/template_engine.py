from __future__ import annotations

from pathlib import Path

from .common import ROOT_DIR

TEMPLATE_DIR = ROOT_DIR / "scripts" / "templates"

try:
    from jinja2 import Environment, FileSystemLoader  # type: ignore
except Exception as exc:  # pragma: no cover - required dependency
    raise RuntimeError(
        "Missing template dependency `jinja2`. "
        "Install build requirements with: python3 -m pip install -r requirements.txt"
    ) from exc


def render_template(template_name: str, context: dict[str, object]) -> str:
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=False)
    template = env.get_template(template_name)
    return template.render(**context)
