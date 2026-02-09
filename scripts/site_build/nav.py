from __future__ import annotations

from .common import (
    NAV_BLOG_END_MARKER,
    NAV_BLOG_START_MARKER,
    NAV_TEACHING_END_MARKER,
    NAV_TEACHING_START_MARKER,
    escape_html,
    indent_block,
)
from .index_ops import update_index_block

def published_courses_for_nav(courses: list[dict[str, object]]) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for course in courses:
        if not bool(course.get("published", False)):
            continue
        slug = str(course.get("slug", "")).strip()
        code = str(course.get("code", "")).strip()
        title = str(course.get("title", "")).strip()
        if not slug or not code or not title:
            continue
        entries.append(
            {
                "slug": slug,
                "label": f"{code} {title}",
            }
        )
    return entries

def recent_posts_for_nav(posts: list[dict[str, object]], limit: int = 3) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for post in posts[: max(limit, 0)]:
        slug = str(post.get("slug", "")).strip()
        title = str(post.get("title", "")).strip()
        if not slug or not title:
            continue
        entries.append({"slug": slug, "label": title})
    return entries

def render_nav_dropdown_items(
    items: list[dict[str, str]],
    active_href: str = "",
) -> str:
    lines: list[str] = []
    for item in items:
        href = str(item.get("href", "")).strip()
        label = str(item.get("label", "")).strip()
        if not href or not label:
            continue
        is_active = bool(active_href) and href == active_href
        item_class = "nav-dropdown__item is-active" if is_active else "nav-dropdown__item"
        lines.append(
            f'<a class="{item_class}" href="{escape_html(href)}">{escape_html(label)}</a>'
        )
    return "\n".join(lines)

def render_nav_dropdown(
    label: str,
    items: list[dict[str, str]],
    *,
    active: bool = False,
    active_href: str = "",
) -> str:
    toggle_class = "nav-link nav-dropdown__toggle"
    if active:
        toggle_class += " is-active"
    items_markup = render_nav_dropdown_items(items, active_href=active_href)
    safe_label = escape_html(label)
    return "\n".join(
        [
            '<div class="nav-dropdown">',
            f'  <button class="{toggle_class}" type="button" aria-haspopup="true" aria-expanded="false">{safe_label}</button>',
            f'  <div class="nav-dropdown__menu" role="menu" aria-label="{safe_label} links">',
            indent_block(items_markup, "    "),
            "  </div>",
            "</div>",
        ]
    )

def build_teaching_dropdown_items(
    *,
    directory_href: str,
    course_href_prefix: str,
    published_courses: list[dict[str, str]],
) -> list[dict[str, str]]:
    items: list[dict[str, str]] = [{"href": directory_href, "label": "Course Directory"}]
    items.extend(
        {
            "href": f"{course_href_prefix}{course['slug']}.html",
            "label": course["label"],
        }
        for course in published_courses
    )
    return items

def build_blog_dropdown_items(
    *,
    blog_index_href: str,
    post_href_prefix: str,
    recent_posts: list[dict[str, str]],
) -> list[dict[str, str]]:
    items: list[dict[str, str]] = [
        {
            "href": f"{post_href_prefix}{post['slug']}.html",
            "label": post["label"],
        }
        for post in recent_posts
    ]
    items.append({"href": blog_index_href, "label": "View all posts"})
    return items

def update_index_nav_dropdowns(
    posts: list[dict[str, object]],
    courses: list[dict[str, object]],
) -> None:
    published_courses = published_courses_for_nav(courses)
    recent_posts = recent_posts_for_nav(posts)

    teaching_items = build_teaching_dropdown_items(
        directory_href="teaching/index.html",
        course_href_prefix="teaching/",
        published_courses=published_courses,
    )
    blog_items = build_blog_dropdown_items(
        blog_index_href="blogs/index.html",
        post_href_prefix="blogs/",
        recent_posts=recent_posts,
    )

    update_index_block(
        NAV_TEACHING_START_MARKER,
        NAV_TEACHING_END_MARKER,
        render_nav_dropdown_items(teaching_items),
    )
    update_index_block(
        NAV_BLOG_START_MARKER,
        NAV_BLOG_END_MARKER,
        render_nav_dropdown_items(blog_items),
    )

