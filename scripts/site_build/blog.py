from __future__ import annotations

import json
import re

from .common import BLOG_OUTPUT_DIR, BLOG_SOURCE_DIR, escape_html, format_date, read_ga_measurement_id
from .markdown_render import (
    get_summary,
    markdown_to_html,
    normalize_date,
    parse_front_matter,
    parse_tags,
)
from .page_context import build_base_context
from .template_engine import render_template
from .templates import mathjax_config_script


def render_post_toc(toc_entries: list[dict[str, object]]) -> str:
    if not toc_entries:
        return ""

    items: list[str] = []
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
            (
                f'<li class="{item_class}">'
                f'<a class="post-toc__link" href="#{escape_html(heading_id)}">'
                f"{escape_html(title)}</a></li>"
            )
        )

    if not items:
        return ""

    items_markup = "".join(items)
    return "\n".join(
        [
            '<aside class="panel post-toc" aria-label="Table of contents">',
            '  <p class="post-toc__title">On this page</p>',
            '  <nav class="post-toc__nav">',
            f"    <ol>{items_markup}</ol>",
            "  </nav>",
            "</aside>",
        ]
    )


def post_page_template(
    post: dict[str, object],
    body_html: str,
    ga_id: str,
) -> str:
    tags_markup = "".join(
        f'<span class="blog-tag">{escape_html(tag)}</span>' for tag in post["tags"]
    )
    toc_markup = render_post_toc(
        [entry for entry in post.get("toc", []) if isinstance(entry, dict)]
    )

    post_article_markup = "\n".join(
        [
            '<article class="panel post-card">',
            '  <div class="post-body">',
            body_html,
            "  </div>",
            "</article>",
        ]
    )
    if toc_markup:
        post_content_markup = "\n".join(
            [
                '<div class="post-layout">',
                toc_markup,
                post_article_markup,
                "</div>",
            ]
        )
    else:
        post_content_markup = post_article_markup

    main_html = render_template(
        "pages/blog_post.html.j2",
        {
            "post_eyebrow": escape_html(str(post.get("eyebrow", "Research Notes"))),
            "post_title": escape_html(str(post["title"])),
            "post_date_iso": escape_html(str(post["date"])),
            "post_date_label": format_date(str(post["date"])),
            "tags_html": tags_markup,
            "post_summary": escape_html(str(post["summary"])),
            "post_content_html": post_content_markup,
        },
    )

    return render_template(
        "base.html.j2",
        build_base_context(
            ga_id=ga_id,
            page_id="blog-post",
            page_title=f"{str(post['title'])} | Wei You",
            meta_description=str(post["summary"]),
            include_cn_fonts=False,
            css_href="../css/site.css",
            js_prefix="../js/",
            brand_href="../index.html#home",
            home_href="../index.html#home",
            research_href="../index.html#research",
            talks_href="../index.html#talks",
            team_href="../index.html#team",
            about_href="../index.html#about",
            teaching_href="../index.html#teaching",
            blog_href="../index.html#blog",
            main_html=main_html,
            page_scripts=["pages/blog_post.js"],
            extra_head_html="",
            extra_before_scripts_html=mathjax_config_script(include_chtml=True),
            extra_after_scripts_html="",
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


def write_blog_output(posts: list[dict[str, object]]) -> None:
    BLOG_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ga_id = read_ga_measurement_id()

    manifest = [
        {
            "title": post["title"],
            "slug": post["slug"],
            "date": post["date"],
            "summary": post["summary"],
            "tags": post["tags"],
        }
        for post in posts
    ]

    (BLOG_OUTPUT_DIR / "posts.js").write_text(
        "window.__BLOG_POSTS__ = " + json.dumps(manifest, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )
    stale_manifest_path = BLOG_OUTPUT_DIR / "posts.json"
    if stale_manifest_path.exists():
        stale_manifest_path.unlink()
    stale_index_path = BLOG_OUTPUT_DIR / "index.html"
    if stale_index_path.exists():
        stale_index_path.unlink()

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


def build_blog(posts: list[dict[str, object]]) -> int:
    write_blog_output(posts)

    print(f"Built {len(posts)} blog post(s).")
    print("Generated: blogs/posts.js")
    return len(posts)
