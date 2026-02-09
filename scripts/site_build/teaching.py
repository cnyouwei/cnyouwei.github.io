from __future__ import annotations

import json
import re

from .common import TEACHING_DATA_PATH, TEACHING_OUTPUT_DIR, escape_html, indent_block, read_ga_measurement_id
from .nav import (
    build_blog_dropdown_items,
    build_teaching_dropdown_items,
    published_courses_for_nav,
    render_nav_dropdown,
)
from .template_engine import render_template
from .templates import font_stylesheet_href, theme_bootstrap_script


def ensure_list_of_strings(value: object) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("Expected a list of strings.")
    output: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ValueError(f"Expected string item, got: {item!r}")
        stripped = item.strip()
        if stripped:
            output.append(stripped)
    return output


def normalize_teaching_path(url: str) -> str:
    stripped = url.strip()
    if not stripped:
        return stripped
    if re.match(r"^(https?:|mailto:|#|/)", stripped):
        return stripped
    if stripped.startswith("../") or stripped.startswith("./"):
        return stripped
    return "../" + stripped


def validate_course(course: dict[str, object]) -> None:
    required = ["slug", "code", "title", "period"]
    missing = [field for field in required if not str(course.get(field, "")).strip()]
    if missing:
        raise ValueError(f"Course missing required fields {missing}: {course}")

    slug = str(course["slug"]).strip()
    if not re.fullmatch(r"[a-z0-9-]+", slug):
        raise ValueError(f"Invalid course slug `{slug}`. Use lowercase letters, digits, and hyphens.")

    published = course.get("published", False)
    if not isinstance(published, bool):
        raise ValueError(f"`published` must be boolean in course {slug}")

    outcomes = course.get("outcomes", [])
    if outcomes is not None and not isinstance(outcomes, list):
        raise ValueError(f"`outcomes` must be a list in course {slug}")

    modules = course.get("modules", [])
    if modules is not None and not isinstance(modules, list):
        raise ValueError(f"`modules` must be a list in course {slug}")

    for module in modules:
        if not isinstance(module, dict):
            raise ValueError(f"Each module must be an object in course {slug}")
        module_required = ["code", "title", "description", "link_label", "link_url"]
        module_missing = [field for field in module_required if not str(module.get(field, "")).strip()]
        if module_missing:
            raise ValueError(f"Module missing fields {module_missing} in course {slug}: {module}")


def load_teaching_data() -> list[dict[str, object]]:
    if not TEACHING_DATA_PATH.exists():
        return []

    payload = json.loads(TEACHING_DATA_PATH.read_text(encoding="utf-8"))
    courses = payload.get("courses", [])
    if not isinstance(courses, list):
        raise ValueError("`courses` must be a list in content/teaching/courses.json")

    normalized: list[dict[str, object]] = []
    for course in courses:
        if not isinstance(course, dict):
            raise ValueError(f"Each course must be an object, got: {course!r}")
        validate_course(course)
        normalized.append(course)
    return normalized


def _base_context(
    *,
    ga_id: str,
    page_id: str,
    page_title: str,
    meta_description: str,
    nav_teaching_html: str,
    nav_blog_html: str,
    main_html: str,
) -> dict[str, str]:
    return {
        "ga_id": escape_html(ga_id),
        "page_id": escape_html(page_id),
        "page_title": page_title,
        "meta_description": meta_description,
        "fonts_href": font_stylesheet_href(include_cn=True),
        "theme_bootstrap_html": theme_bootstrap_script(),
        "css_href": "../css/site.css",
        "brand_href": "../index.html#home",
        "home_href": "../index.html#home",
        "research_href": "../index.html#research",
        "talks_href": "../index.html#talks",
        "team_href": "../index.html#team",
        "about_href": "../index.html#about",
        "nav_teaching_html": indent_block(nav_teaching_html, "          "),
        "nav_blog_html": indent_block(nav_blog_html, "          "),
        "main_html": main_html,
        "js_prefix": "../js/",
        "extra_head_html": "",
        "extra_before_scripts_html": "",
        "extra_after_scripts_html": "",
    }


def teaching_index_template(
    courses: list[dict[str, object]],
    ga_id: str,
    recent_posts: list[dict[str, str]],
) -> str:
    cards: list[str] = []
    for course in courses:
        code = escape_html(str(course["code"]))
        title = escape_html(str(course["title"]))
        period = escape_html(str(course["period"]))
        summary = escape_html(str(course.get("summary", "")).strip() or "Course page in preparation.")
        slug = escape_html(str(course["slug"]))
        published = bool(course.get("published", False))

        action = (
            f'<a class="button" href="./{slug}.html">Open course page</a>'
            if published
            else '<p class="muted">Course page coming soon.</p>'
        )
        status = "Published" if published else "Coming Soon"
        status_class = "is-live" if published else "is-soon"

        cards.append(
            "\n".join(
                [
                    '<article class="module-card course-card">',
                    f'  <p class="timeline-year">{period}</p>',
                    f'  <p class="course-status {status_class}">{status}</p>',
                    f"  <h3>{code} {title}</h3>",
                    f"  <p>{summary}</p>",
                    f"  {action}",
                    "</article>",
                ]
            )
        )

    cards_html = "\n".join(cards)
    if not cards_html:
        cards_html = (
            '<article class="module-card course-card"><h3>No courses yet</h3>'
            "<p>Add entries to content/teaching/courses.json and rebuild.</p></article>"
        )

    teaching_dropdown_items = build_teaching_dropdown_items(
        directory_href="./index.html",
        course_href_prefix="./",
        published_courses=published_courses_for_nav(courses),
    )
    blog_dropdown_items = build_blog_dropdown_items(
        blog_index_href="../blogs/index.html",
        post_href_prefix="../blogs/",
        recent_posts=recent_posts,
    )

    teaching_dropdown = render_nav_dropdown(
        "Teaching",
        teaching_dropdown_items,
        active=True,
        active_href="./index.html",
    )
    blog_dropdown = render_nav_dropdown("Blog", blog_dropdown_items)

    main_html = render_template(
        "pages/teaching_index.html.j2",
        {
            "cards_html": indent_block(cards_html, "          "),
        },
    )

    return render_template(
        "base.html.j2",
        _base_context(
            ga_id=ga_id,
            page_id="teaching-index",
            page_title="Teaching | Wei You",
            meta_description="Course pages and teaching materials by Wei You.",
            nav_teaching_html=teaching_dropdown,
            nav_blog_html=blog_dropdown,
            main_html=main_html,
        ),
    )


def teaching_course_template(
    course: dict[str, object],
    ga_id: str,
    recent_posts: list[dict[str, str]],
    published_courses: list[dict[str, str]],
) -> str:
    code = escape_html(str(course["code"]))
    title = escape_html(str(course["title"]))
    period = escape_html(str(course["period"]))
    summary = escape_html(str(course.get("summary", "")).strip())
    overview = escape_html(str(course.get("overview", "")).strip() or str(course.get("summary", "")).strip())
    audience = escape_html(str(course.get("audience", "")).strip() or "Undergraduate/graduate students.")
    prerequisites = escape_html(str(course.get("prerequisites", "")).strip() or "See syllabus.")

    outcomes = ensure_list_of_strings(course.get("outcomes", []))
    modules = course.get("modules", [])
    if not isinstance(modules, list):
        modules = []

    module_cards: list[str] = []
    for module in modules:
        if not isinstance(module, dict):
            continue
        module_code = escape_html(str(module.get("code", "")).strip())
        module_title = escape_html(str(module.get("title", "")).strip())
        module_desc = escape_html(str(module.get("description", "")).strip())
        link_label = escape_html(str(module.get("link_label", "")).strip() or "Open resource")
        link_url = normalize_teaching_path(str(module.get("link_url", "")).strip())
        safe_url = escape_html(link_url)
        module_cards.append(
            "\n".join(
                [
                    '<article class="module-card">',
                    f'  <p class="module-code">{module_code}</p>',
                    f"  <h3>{module_title}</h3>",
                    f"  <p>{module_desc}</p>",
                    f'  <a class="button" href="{safe_url}" target="_blank" rel="noopener noreferrer">{link_label}</a>',
                    "</article>",
                ]
            )
        )

    modules_html = "\n".join(module_cards)
    if not modules_html:
        modules_html = (
            '<article class="module-card"><h3>No modules published yet</h3>'
            "<p>Materials will be added here when available.</p></article>"
        )

    outcomes_items = "".join(f"<li>{escape_html(item)}</li>" for item in outcomes)
    if not outcomes_items:
        outcomes_items = "<li>Learning outcomes will be posted soon.</li>"

    current_slug = str(course["slug"]).strip()
    teaching_dropdown_items = build_teaching_dropdown_items(
        directory_href="./index.html",
        course_href_prefix="./",
        published_courses=published_courses,
    )
    blog_dropdown_items = build_blog_dropdown_items(
        blog_index_href="../blogs/index.html",
        post_href_prefix="../blogs/",
        recent_posts=recent_posts,
    )

    teaching_dropdown = render_nav_dropdown(
        "Teaching",
        teaching_dropdown_items,
        active=True,
        active_href=f"./{current_slug}.html",
    )
    blog_dropdown = render_nav_dropdown("Blog", blog_dropdown_items)

    main_html = render_template(
        "pages/teaching_course.html.j2",
        {
            "course_heading": f"{code}: {title}",
            "course_overview": overview,
            "course_period": period,
            "course_audience": audience,
            "course_prerequisites": prerequisites,
            "outcomes_items_html": indent_block(outcomes_items, "            "),
            "modules_html": indent_block(modules_html, "          "),
        },
    )

    return render_template(
        "base.html.j2",
        _base_context(
            ga_id=ga_id,
            page_id="teaching-course",
            page_title=f"{code} {title} | Teaching",
            meta_description=summary,
            nav_teaching_html=teaching_dropdown,
            nav_blog_html=blog_dropdown,
            main_html=main_html,
        ),
    )


def build_teaching(courses: list[dict[str, object]], recent_posts: list[dict[str, str]]) -> int:
    ga_id = read_ga_measurement_id()
    published_courses = published_courses_for_nav(courses)

    TEACHING_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (TEACHING_OUTPUT_DIR / "index.html").write_text(
        teaching_index_template(courses, ga_id, recent_posts),
        encoding="utf-8",
    )

    generated = 0
    for course in courses:
        if not bool(course.get("published", False)):
            continue
        slug = str(course["slug"]).strip()
        output_path = TEACHING_OUTPUT_DIR / f"{slug}.html"
        output_path.write_text(
            teaching_course_template(
                course,
                ga_id,
                recent_posts,
                published_courses,
            ),
            encoding="utf-8",
        )
        generated += 1

    print(f"Built teaching directory from {len(courses)} course entry(ies).")
    print(f"Generated: teaching/index.html and {generated} course page(s).")
    return len(courses)
