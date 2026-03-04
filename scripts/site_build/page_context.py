from __future__ import annotations

from .common import escape_html
from .templates import font_stylesheet_href, theme_bootstrap_script

SUBPAGE_HOME_HREF = "../index.html#home"
SUBPAGE_RESEARCH_HREF = "../index.html#research"
SUBPAGE_TALKS_HREF = "../index.html#talks"
SUBPAGE_TEACHING_HREF = "../index.html#teaching"
SUBPAGE_TEAM_HREF = "../index.html#team"
SUBPAGE_ABOUT_HREF = "../index.html#about"
SUBPAGE_BLOG_HREF = "../index.html#blog"


def _resolve_script_src(js_prefix: str, script_path: str) -> str:
    path = script_path.strip()
    if not path:
        return ""
    if path.startswith(("http://", "https://", "/", "./", "../")):
        return path
    return js_prefix + path


def _render_page_scripts(js_prefix: str, page_scripts: list[str] | tuple[str, ...]) -> str:
    lines: list[str] = []
    for script_path in page_scripts:
        if not isinstance(script_path, str):
            continue
        src = _resolve_script_src(js_prefix, script_path)
        if not src:
            continue
        lines.append(f'  <script src="{escape_html(src)}" defer></script>')
    return "\n".join(lines)


def build_base_context(
    *,
    ga_id: str,
    page_id: str,
    page_title: str,
    meta_description: str,
    include_cn_fonts: bool,
    css_href: str,
    js_prefix: str,
    brand_href: str,
    home_href: str,
    research_href: str,
    talks_href: str,
    teaching_href: str,
    team_href: str,
    about_href: str,
    blog_href: str,
    main_html: str,
    brand_aria_label: str = "",
    page_scripts: list[str] | tuple[str, ...] = (),
    extra_head_html: str = "",
    extra_before_scripts_html: str = "",
    extra_after_scripts_html: str = "",
) -> dict[str, str]:
    return {
        "ga_id": escape_html(ga_id),
        "page_id": escape_html(page_id),
        "page_title": escape_html(page_title),
        "meta_description": escape_html(meta_description),
        "fonts_href": font_stylesheet_href(include_cn=include_cn_fonts),
        "theme_bootstrap_html": theme_bootstrap_script(),
        "css_href": escape_html(css_href),
        "brand_href": escape_html(brand_href),
        "brand_aria_label": escape_html(brand_aria_label),
        "home_href": escape_html(home_href),
        "research_href": escape_html(research_href),
        "talks_href": escape_html(talks_href),
        "team_href": escape_html(team_href),
        "about_href": escape_html(about_href),
        "teaching_href": escape_html(teaching_href),
        "blog_href": escape_html(blog_href),
        "main_html": main_html,
        "js_prefix": escape_html(js_prefix),
        "page_scripts_html": _render_page_scripts(js_prefix, page_scripts),
        "extra_head_html": extra_head_html,
        "extra_before_scripts_html": extra_before_scripts_html,
        "extra_after_scripts_html": extra_after_scripts_html,
    }


def build_subpage_context(
    *,
    ga_id: str,
    page_id: str,
    page_title: str,
    meta_description: str,
    main_html: str,
    page_scripts: list[str] | tuple[str, ...] = (),
    extra_head_html: str = "",
    extra_before_scripts_html: str = "",
    extra_after_scripts_html: str = "",
) -> dict[str, str]:
    return build_base_context(
        ga_id=ga_id,
        page_id=page_id,
        page_title=page_title,
        meta_description=meta_description,
        include_cn_fonts=True,
        css_href="../css/site.css",
        js_prefix="../js/",
        brand_href=SUBPAGE_HOME_HREF,
        brand_aria_label="",
        home_href=SUBPAGE_HOME_HREF,
        research_href=SUBPAGE_RESEARCH_HREF,
        talks_href=SUBPAGE_TALKS_HREF,
        teaching_href=SUBPAGE_TEACHING_HREF,
        team_href=SUBPAGE_TEAM_HREF,
        about_href=SUBPAGE_ABOUT_HREF,
        blog_href=SUBPAGE_BLOG_HREF,
        main_html=main_html,
        page_scripts=page_scripts,
        extra_head_html=extra_head_html,
        extra_before_scripts_html=extra_before_scripts_html,
        extra_after_scripts_html=extra_after_scripts_html,
    )
