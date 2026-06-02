from __future__ import annotations

import json
import re

from .common import TEACHING_DATA_PATH, TEACHING_OUTPUT_DIR, escape_html, page_context
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
    normalized_courses: list[dict[str, object]] = []

    for course in courses:
        code = escape_html(str(course["code"]))
        title = escape_html(str(course["title"]))
        normalized_courses.append(
            {
                "period": escape_html(str(course["period"])),
                "institution": escape_html(
                    str(course.get("institution", "")).strip() or "Institution TBD"
                ),
                "status": "Published" if bool(course.get("published", False)) else "Coming Soon",
                "status_class": "is-live" if bool(course.get("published", False)) else "is-soon",
                "heading": f"{code} {title}",
                "summary": escape_html(
                    str(course.get("summary", "")).strip() or "Course page in preparation."
                ),
                "slug": escape_html(str(course["slug"])),
                "published": bool(course.get("published", False)),
            }
        )

    return render_template(
        "partials/teaching_home_cards.html.j2",
        {"courses": normalized_courses},
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
    overview = escape_html(str(course.get("overview", "")).strip() or summary_raw)
    audience = escape_html(str(course.get("audience", "")).strip() or "Undergraduate/graduate students.")
    prerequisites = escape_html(str(course.get("prerequisites", "")).strip() or "See syllabus.")

    outcomes = [escape_html(item) for item in ensure_list_of_strings(course.get("outcomes", []))]

    modules_raw = course.get("modules", [])
    modules: list[dict[str, str]] = []
    if isinstance(modules_raw, list):
        for module in modules_raw:
            if not isinstance(module, dict):
                continue
            link_url = normalize_teaching_path(str(module.get("link_url", "")).strip())
            modules.append(
                {
                    "code": escape_html(str(module.get("code", "")).strip()),
                    "title": escape_html(str(module.get("title", "")).strip()),
                    "description": escape_html(str(module.get("description", "")).strip()),
                    "link_label": escape_html(
                        str(module.get("link_label", "")).strip() or "Open resource"
                    ),
                    "url": escape_html(link_url),
                }
            )

    outcomes_items_html = render_template(
        "partials/teaching_outcomes_items.html.j2",
        {"outcomes": outcomes},
    )
    modules_html = render_template(
        "partials/teaching_module_cards.html.j2",
        {"modules": modules},
    )

    main_html = render_template(
        "pages/teaching_course.html.j2",
        {
            "course_heading": f"{code}: {title}",
            "course_institution": institution,
            "course_overview": overview,
            "course_period": period,
            "course_audience": audience,
            "course_prerequisites": prerequisites,
            "outcomes_items_html": outcomes_items_html,
            "modules_html": modules_html,
        },
    )

    return render_template(
        "base.html.j2",
        page_context(
            ga_id=ga_id,
            page_id="teaching-course",
            page_title=f"{raw_code} {raw_title} | Teaching",
            meta_description=summary_raw,
            main_html=main_html,
            subpage=True,
        ),
    )


def build_teaching(courses: list[dict[str, object]], ga_id: str) -> int:
    TEACHING_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stale_index_path = TEACHING_OUTPUT_DIR / "index.html"
    if stale_index_path.exists():
        stale_index_path.unlink()

    expected_html_files = {
        f"{str(course['slug']).strip()}.html"
        for course in courses
        if bool(course.get("published", False))
    }
    for existing in TEACHING_OUTPUT_DIR.glob("*.html"):
        if existing.name not in expected_html_files:
            existing.unlink()

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

    print(f"Loaded {len(courses)} teaching course entry(ies).")
    print(f"Generated: {generated} teaching course page(s).")
    return len(courses)
