from __future__ import annotations

import re

from .common import BLOG_OUTPUT_DIR, BLOG_SOURCE_DIR, escape_html, format_date
from .markdown_render import (
    get_summary,
    markdown_to_html,
    normalize_date,
    parse_front_matter,
    parse_tags,
)
from .page_context import build_subpage_context
from .template_engine import render_template
from .templates import mathjax_config_script


def _normalized_toc_entries(toc_entries: list[dict[str, object]]) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    for entry in toc_entries:
        heading_id = str(entry.get("id", "")).strip()
        title = str(entry.get("title", "")).strip()
        level = int(entry.get("level", 2))
        if not heading_id or not title:
            continue
        item_class = "post-toc__item"
        if level >= 3:
            item_class += " post-toc__item--sub"
        items.append(
            {
                "item_class": item_class,
                "heading_id": escape_html(heading_id),
                "title": escape_html(title),
            }
        )
    return items


def render_post_toc(toc_entries: list[dict[str, object]]) -> str:
    items = _normalized_toc_entries(toc_entries)
    if not items:
        return ""
    return render_template("partials/blog_post_toc.html.j2", {"toc_items": items})


def render_recent_posts_markup(posts: list[dict[str, object]]) -> str:
    normalized_posts: list[dict[str, object]] = []
    for post in posts:
        tags = post.get("tags", [])
        post_tags = [escape_html(str(tag)) for tag in tags[:2]] if isinstance(tags, list) else []
        normalized_posts.append(
            {
                "title": escape_html(str(post.get("title", ""))),
                "slug": escape_html(str(post.get("slug", ""))),
                "date_iso": escape_html(str(post.get("date", ""))),
                "date_label": format_date(str(post.get("date", ""))),
                "summary": escape_html(str(post.get("summary", ""))),
                "tags": post_tags,
            }
        )

    return render_template("partials/blog_recent_posts.html.j2", {"posts": normalized_posts})


def post_page_template(
    post: dict[str, object],
    body_html: str,
    ga_id: str,
) -> str:
    tags_markup = "".join(
        f'<span class="blog-tag">{escape_html(str(tag))}</span>' for tag in post["tags"]
    )
    toc_markup = render_post_toc(
        [entry for entry in post.get("toc", []) if isinstance(entry, dict)]
    )

    main_html = render_template(
        "pages/blog_post.html.j2",
        {
            "post_eyebrow": escape_html(str(post.get("eyebrow", "Research Notes"))),
            "post_title": escape_html(str(post["title"])),
            "post_date_iso": escape_html(str(post["date"])),
            "post_date_label": format_date(str(post["date"])),
            "tags_html": tags_markup,
            "post_summary": escape_html(str(post["summary"])),
            "post_body_html": body_html,
            "post_toc_html": toc_markup,
            "has_post_toc": bool(toc_markup),
        },
    )

    return render_template(
        "base.html.j2",
        build_subpage_context(
            ga_id=ga_id,
            page_id="blog-post",
            page_title=f"{str(post['title'])} | Wei You",
            meta_description=str(post["summary"]),
            main_html=main_html,
            page_scripts=["pages/blog_post.js"],
            extra_before_scripts_html=mathjax_config_script(include_chtml=True),
        ),
    )


def read_source_posts() -> list[dict[str, object]]:
    if not BLOG_SOURCE_DIR.exists():
        return []

    posts: list[dict[str, object]] = []
    for source_file in sorted(BLOG_SOURCE_DIR.glob("*.md")):
        raw = source_file.read_text(encoding="utf-8")
        meta, body = parse_front_matter(raw)

        stem = source_file.stem
        date_from_name_match = re.match(r"^(\d{4}-\d{2}-\d{2})", stem)
        date_from_name = date_from_name_match.group(1) if date_from_name_match else None

        slug = meta.get("slug", stem).strip()
        title = meta.get("title", stem.replace("-", " ")).strip()
        date = normalize_date(meta.get("date", "").strip(), date_from_name)
        summary = get_summary(meta.get("summary", "").strip(), body)
        tags = parse_tags(meta.get("tags", ""))
        eyebrow = meta.get("eyebrow", "").strip() or "Research Notes"
        html_body, toc_entries = markdown_to_html(body)

        posts.append(
            {
                "title": title,
                "slug": slug,
                "date": date,
                "summary": summary,
                "tags": tags,
                "eyebrow": eyebrow,
                "html": html_body,
                "toc": toc_entries,
            }
        )

    posts.sort(key=lambda item: (item["date"], item["title"]), reverse=True)
    return posts


def write_blog_output(posts: list[dict[str, object]], ga_id: str) -> None:
    BLOG_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    stale_manifest_path = BLOG_OUTPUT_DIR / "posts.js"
    if stale_manifest_path.exists():
        stale_manifest_path.unlink()
    stale_json_manifest_path = BLOG_OUTPUT_DIR / "posts.json"
    if stale_json_manifest_path.exists():
        stale_json_manifest_path.unlink()
    stale_index_path = BLOG_OUTPUT_DIR / "index.html"
    if stale_index_path.exists():
        stale_index_path.unlink()

    expected_html_files = {f"{post['slug']}.html" for post in posts}
    for existing in BLOG_OUTPUT_DIR.glob("*.html"):
        if existing.name not in expected_html_files:
            existing.unlink()

    for post in posts:
        output_path = BLOG_OUTPUT_DIR / f"{post['slug']}.html"
        output_path.write_text(
            post_page_template(
                post,
                post["html"],
                ga_id,
            ),
            encoding="utf-8",
        )


def build_blog(posts: list[dict[str, object]], ga_id: str) -> int:
    write_blog_output(posts, ga_id)

    print(f"Built {len(posts)} blog post(s).")
    return len(posts)
