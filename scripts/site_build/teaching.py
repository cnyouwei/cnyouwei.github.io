from __future__ import annotations

import json
import re

from .common import (
    TEACHING_DATA_PATH,
    TEACHING_HOME_END_MARKER,
    TEACHING_HOME_START_MARKER,
    TEACHING_OUTPUT_DIR,
    escape_html,
    indent_block,
    read_ga_measurement_id,
)
from .index_ops import update_index_block
from .page_context import build_base_context
from .template_engine import render_template


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

    institution = course.get("institution", "")
    if institution is not None and not isinstance(institution, str):
        raise ValueError(f"`institution` must be a string in course {slug}")

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


def render_home_teaching_markup(courses: list[dict[str, object]]) -> str:
    cards: list[str] = []

    for course in courses:
        code = escape_html(str(course["code"]))
        title = escape_html(str(course["title"]))
        period = escape_html(str(course["period"]))
        institution = escape_html(str(course.get("institution", "")).strip() or "Institution TBD")
        summary = escape_html(str(course.get("summary", "")).strip() or "Course page in preparation.")
        slug = escape_html(str(course["slug"]))
        published = bool(course.get("published", False))

        action = (
            f'<a class="button" href="teaching/{slug}.html">Open course page</a>'
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
                    f'  <p class="course-institution">{institution}</p>',
                    f'  <p class="course-status {status_class}">{status}</p>',
                    f"  <h3>{code} {title}</h3>",
                    f"  <p>{summary}</p>",
                    f"  {action}",
                    "</article>",
                ]
            )
        )

    if not cards:
        cards.append(
            '<article class="module-card course-card"><h3>No courses yet</h3>'
            '<p>Add entries to content/teaching/courses.json and rebuild.</p></article>'
        )

    cards_html = "\n".join(cards)
    return "\n".join(
        [
            '<section class="module-section reveal-up delay-1" aria-label="Teaching courses">',
            '  <div class="module-grid">',
            indent_block(cards_html, "    "),
            "  </div>",
            "</section>",
        ]
    )


def update_home_teaching_section(courses: list[dict[str, object]]) -> None:
    update_index_block(
        TEACHING_HOME_START_MARKER,
        TEACHING_HOME_END_MARKER,
        render_home_teaching_markup(courses),
    )


def teaching_course_template(
    course: dict[str, object],
    ga_id: str,
) -> str:
    raw_code = str(course["code"]).strip()
    raw_title = str(course["title"]).strip()
    code = escape_html(raw_code)
    title = escape_html(raw_title)
    period = escape_html(str(course["period"]))
    institution = escape_html(str(course.get("institution", "")).strip() or "Institution TBD")
    summary_raw = str(course.get("summary", "")).strip()
    summary = escape_html(summary_raw)
    overview = escape_html(str(course.get("overview", "")).strip() or summary_raw)
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

    main_html = render_template(
        "pages/teaching_course.html.j2",
        {
            "course_heading": f"{code}: {title}",
            "course_institution": institution,
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
        build_base_context(
            ga_id=ga_id,
            page_id="teaching-course",
            page_title=f"{raw_code} {raw_title} | Teaching",
            meta_description=summary_raw,
            include_cn_fonts=True,
            css_href="../css/site.css",
            js_prefix="../js/",
            brand_href="../index.html#home",
            home_href="../index.html#home",
            research_href="../index.html#research",
            talks_href="../index.html#talks",
            teaching_href="../index.html#teaching",
            team_href="../index.html#team",
            about_href="../index.html#about",
            blog_href="../index.html#blog",
            main_html=main_html,
            page_scripts=[],
        ),
    )


def build_teaching(courses: list[dict[str, object]]) -> int:
    ga_id = read_ga_measurement_id()

    update_home_teaching_section(courses)

    TEACHING_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stale_index_path = TEACHING_OUTPUT_DIR / "index.html"
    if stale_index_path.exists():
        stale_index_path.unlink()

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
            ),
            encoding="utf-8",
        )
        generated += 1

    print(f"Built teaching home section from {len(courses)} course entry(ies).")
    print(f"Generated: {generated} teaching course page(s).")
    print("Updated: index.html")
    return len(courses)
