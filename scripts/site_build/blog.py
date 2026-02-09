from __future__ import annotations

import json
import re

from .common import BLOG_OUTPUT_DIR, BLOG_SOURCE_DIR, escape_html, format_date, indent_block, read_ga_measurement_id
from .markdown_render import (
    get_summary,
    markdown_to_html,
    normalize_date,
    parse_front_matter,
    parse_tags,
)
from .nav import (
    build_blog_dropdown_items,
    build_teaching_dropdown_items,
    published_courses_for_nav,
    recent_posts_for_nav,
    render_nav_dropdown,
)
from .template_engine import render_template
from .templates import (
    font_stylesheet_href,
    mathjax_config_script,
    theme_bootstrap_script,
)


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


def _base_context(
    *,
    ga_id: str,
    page_id: str,
    page_title: str,
    meta_description: str,
    css_href: str,
    js_prefix: str,
    brand_href: str,
    home_href: str,
    research_href: str,
    talks_href: str,
    team_href: str,
    about_href: str,
    nav_teaching_html: str,
    nav_blog_html: str,
    main_html: str,
    extra_head_html: str = "",
    extra_before_scripts_html: str = "",
    extra_after_scripts_html: str = "",
) -> dict[str, str]:
    return {
        "ga_id": escape_html(ga_id),
        "page_id": escape_html(page_id),
        "page_title": page_title,
        "meta_description": meta_description,
        "fonts_href": font_stylesheet_href(include_cn=False),
        "theme_bootstrap_html": theme_bootstrap_script(),
        "css_href": css_href,
        "brand_href": brand_href,
        "home_href": home_href,
        "research_href": research_href,
        "talks_href": talks_href,
        "team_href": team_href,
        "about_href": about_href,
        "nav_teaching_html": indent_block(nav_teaching_html, "          "),
        "nav_blog_html": indent_block(nav_blog_html, "          "),
        "main_html": main_html,
        "js_prefix": js_prefix,
        "extra_head_html": extra_head_html,
        "extra_before_scripts_html": extra_before_scripts_html,
        "extra_after_scripts_html": extra_after_scripts_html,
    }


def post_page_template(
    post: dict[str, object],
    body_html: str,
    ga_id: str,
    recent_posts: list[dict[str, str]],
    published_courses: list[dict[str, str]],
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
            "post_title": escape_html(str(post["title"])),
            "post_date_iso": escape_html(str(post["date"])),
            "post_date_label": format_date(str(post["date"])),
            "tags_html": tags_markup,
            "post_summary": escape_html(str(post["summary"])),
            "post_content_html": post_content_markup,
        },
    )

    teaching_dropdown_items = build_teaching_dropdown_items(
        directory_href="../teaching/index.html",
        course_href_prefix="../teaching/",
        published_courses=published_courses,
    )
    blog_dropdown_items = build_blog_dropdown_items(
        blog_index_href="./index.html",
        post_href_prefix="./",
        recent_posts=recent_posts,
    )

    teaching_dropdown = render_nav_dropdown("Teaching", teaching_dropdown_items)
    blog_dropdown = render_nav_dropdown(
        "Blog",
        blog_dropdown_items,
        active=True,
        active_href=f"./{str(post['slug']).strip()}.html",
    )

    return render_template(
        "base.html.j2",
        _base_context(
            ga_id=ga_id,
            page_id="blog-post",
            page_title=f"{escape_html(str(post['title']))} | Wei You",
            meta_description=escape_html(str(post["summary"])),
            css_href="../css/site.css",
            js_prefix="../js/",
            brand_href="../index.html#home",
            home_href="../index.html#home",
            research_href="../index.html#research",
            talks_href="../index.html#talks",
            team_href="../index.html#team",
            about_href="../index.html#about",
            nav_teaching_html=teaching_dropdown,
            nav_blog_html=blog_dropdown,
            main_html=main_html,
            extra_head_html="",
            extra_before_scripts_html=mathjax_config_script(include_chtml=True),
            extra_after_scripts_html="",
        ),
    )


def blog_index_template(
    posts: list[dict[str, object]],
    ga_id: str,
    published_courses: list[dict[str, str]],
) -> str:
    cards: list[str] = []

    for post in posts:
        tags_markup = "".join(
            f'<span class="blog-tag">{escape_html(tag)}</span>' for tag in post["tags"][:3]
        )
        cards.append(
            f"""<article class=\"module-card blog-card\">
  <div class=\"blog-meta\"><time datetime=\"{post['date']}\">{format_date(post['date'])}</time>{tags_markup}</div>
  <h3><a href=\"./{post['slug']}.html\">{escape_html(post['title'])}</a></h3>
  <p>{escape_html(post['summary'])}</p>
  <a class=\"button\" href=\"./{post['slug']}.html\">Read post</a>
</article>"""
        )

    card_markup = "\n".join(cards)
    if not card_markup:
        card_markup = (
            '<article class="module-card blog-card"><h3>No posts yet</h3><p>Add a markdown file under '
            'content/blog and rerun the build script.</p></article>'
        )

    main_html = render_template(
        "pages/blog_index.html.j2",
        {
            "cards_html": indent_block(card_markup, "          "),
        },
    )

    recent_posts = recent_posts_for_nav(posts)
    teaching_dropdown_items = build_teaching_dropdown_items(
        directory_href="../teaching/index.html",
        course_href_prefix="../teaching/",
        published_courses=published_courses,
    )
    blog_dropdown_items = build_blog_dropdown_items(
        blog_index_href="./index.html",
        post_href_prefix="./",
        recent_posts=recent_posts,
    )

    teaching_dropdown = render_nav_dropdown("Teaching", teaching_dropdown_items)
    blog_dropdown = render_nav_dropdown(
        "Blog",
        blog_dropdown_items,
        active=True,
        active_href="./index.html",
    )

    return render_template(
        "base.html.j2",
        _base_context(
            ga_id=ga_id,
            page_id="blog-index",
            page_title="Blog | Wei You",
            meta_description="Research notes and updates by Wei You.",
            css_href="../css/site.css",
            js_prefix="../js/",
            brand_href="../index.html#home",
            home_href="../index.html#home",
            research_href="../index.html#research",
            talks_href="../index.html#talks",
            team_href="../index.html#team",
            about_href="../index.html#about",
            nav_teaching_html=teaching_dropdown,
            nav_blog_html=blog_dropdown,
            main_html=main_html,
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
        html_body, toc_entries = markdown_to_html(body)

        posts.append(
            {
                "title": title,
                "slug": slug,
                "date": date,
                "summary": summary,
                "tags": tags,
                "html": html_body,
                "toc": toc_entries,
            }
        )

    posts.sort(key=lambda item: (item["date"], item["title"]), reverse=True)
    return posts


def write_blog_output(posts: list[dict[str, object]], courses: list[dict[str, object]]) -> None:
    BLOG_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ga_id = read_ga_measurement_id()
    published_courses = published_courses_for_nav(courses)

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

    (BLOG_OUTPUT_DIR / "posts.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (BLOG_OUTPUT_DIR / "posts.js").write_text(
        "window.__BLOG_POSTS__ = " + json.dumps(manifest, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )
    (BLOG_OUTPUT_DIR / "index.html").write_text(
        blog_index_template(manifest, ga_id, published_courses), encoding="utf-8"
    )

    recent_posts = recent_posts_for_nav(manifest)
    for post in posts:
        output_path = BLOG_OUTPUT_DIR / f"{post['slug']}.html"
        output_path.write_text(
            post_page_template(
                post,
                post["html"],
                ga_id,
                recent_posts,
                published_courses,
            ),
            encoding="utf-8",
        )


def build_blog(posts: list[dict[str, object]], courses: list[dict[str, object]]) -> int:
    write_blog_output(posts, courses)

    print(f"Built {len(posts)} blog post(s).")
    print("Generated: blogs/index.html")
    print("Generated: blogs/posts.json")
    print("Generated: blogs/posts.js")
    return len(posts)
