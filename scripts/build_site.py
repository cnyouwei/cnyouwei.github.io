#!/usr/bin/env python3
"""Build the static site artifacts.

This script performs both build steps:
1) Build blog outputs from content/blog/*.md
2) Build the Home selected-papers list and Research section in index.html
   from content/research/papers.json
3) Build teaching pages from content/teaching/courses.json
"""

from __future__ import annotations

import datetime as dt
import html
import json
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

# Blog paths
BLOG_SOURCE_DIR = ROOT_DIR / "content" / "blog"
BLOG_OUTPUT_DIR = ROOT_DIR / "blogs"

# Research paths
INDEX_PATH = ROOT_DIR / "index.html"
RESEARCH_DATA_PATH = ROOT_DIR / "content" / "research" / "papers.json"

# Teaching paths
TEACHING_DATA_PATH = ROOT_DIR / "content" / "teaching" / "courses.json"
TEACHING_OUTPUT_DIR = ROOT_DIR / "teaching"

SELECTED_START_MARKER = "<!-- SELECTED-PAPERS:START -->"
SELECTED_END_MARKER = "<!-- SELECTED-PAPERS:END -->"
RESEARCH_START_MARKER = "<!-- RESEARCH-CONTENT:START -->"
RESEARCH_END_MARKER = "<!-- RESEARCH-CONTENT:END -->"
NAV_TEACHING_START_MARKER = "<!-- NAV-TEACHING-DROPDOWN:START -->"
NAV_TEACHING_END_MARKER = "<!-- NAV-TEACHING-DROPDOWN:END -->"
NAV_BLOG_START_MARKER = "<!-- NAV-BLOG-DROPDOWN:START -->"
NAV_BLOG_END_MARKER = "<!-- NAV-BLOG-DROPDOWN:END -->"
GA_ID_PLACEHOLDER = "G-XXXXXXXXXX"

BADGE_LABELS = {
    "working": "Working",
    "journal": "Journal",
    "conference": "Conference",
    "thesis": "Thesis",
}


def escape_html(text: str) -> str:
    return html.escape(text, quote=True)


def read_ga_measurement_id() -> str:
    if not INDEX_PATH.exists():
        return GA_ID_PLACEHOLDER

    index_html = INDEX_PATH.read_text(encoding="utf-8")
    match = re.search(r'<html\b[^>]*\bdata-ga-id="([^"]+)"', index_html, flags=re.IGNORECASE)
    if not match:
        return GA_ID_PLACEHOLDER

    value = match.group(1).strip()
    return value if value else GA_ID_PLACEHOLDER


# ---------------------------------------------------------------------------
# Blog build
# ---------------------------------------------------------------------------

def parse_front_matter(raw: str) -> tuple[dict[str, str], str]:
    if not raw.startswith("---\n"):
        return {}, raw.strip()

    end_index = raw.find("\n---\n", 4)
    if end_index == -1:
        return {}, raw.strip()

    meta_block = raw[4:end_index]
    body = raw[end_index + 5 :].strip()

    meta: dict[str, str] = {}
    for line in meta_block.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        meta[key.strip()] = value.strip()

    return meta, body


def parse_tags(raw_tags: str) -> list[str]:
    if not raw_tags:
        return []

    text = raw_tags.strip()
    if text.startswith("[") and text.endswith("]"):
        text = text[1:-1]

    tags = []
    for item in text.split(","):
        tag = item.strip().strip('"').strip("'")
        if tag:
            tags.append(tag)
    return tags


def inline_markdown_to_html(raw: str) -> str:
    text = escape_html(raw)
    math_tokens: list[str] = []

    def stash_math(match: re.Match[str]) -> str:
        token = f"@@MATH{len(math_tokens)}@@"
        math_tokens.append(match.group(0))
        return token

    # Protect math segments so markdown regexes do not mutate TeX content.
    text = re.sub(r"\\\((.+?)\\\)", stash_math, text)
    text = re.sub(r"\\\[(.+?)\\\]", stash_math, text)
    text = re.sub(r"(?<!\\)\$(?!\$)(.+?)(?<!\\)\$(?!\$)", stash_math, text)

    # Inline code first.
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)

    for idx, segment in enumerate(math_tokens):
        text = text.replace(f"@@MATH{idx}@@", segment)

    return text


def markdown_to_html(markdown: str) -> str:
    lines = markdown.replace("\r\n", "\n").split("\n")
    blocks: list[str] = []
    i = 0

    def render_display_math(delimiter: str, expression: str) -> str:
        safe_expression = escape_html(expression.strip())
        if delimiter == "$$":
            return f"<div class=\"math-display\">$$\n{safe_expression}\n$$</div>"
        return f"<div class=\"math-display\">\\[\n{safe_expression}\n\\]</div>"

    def parse_single_line_display_math(line: str) -> str | None:
        stripped = line.strip()
        match_dollars = re.fullmatch(r"\$\$(.+)\$\$", stripped)
        if match_dollars:
            return render_display_math("$$", match_dollars.group(1))

        match_brackets = re.fullmatch(r"\\\[(.+)\\\]", stripped)
        if match_brackets:
            return render_display_math(r"\[", match_brackets.group(1))

        return None

    def collect_paragraph(start: int) -> tuple[str, int]:
        paragraph_lines = []
        j = start

        while j < len(lines):
            line = lines[j]
            stripped = line.strip()
            if not line.strip():
                break
            if re.match(r"^(#{1,6})\s+", line):
                break
            if line.startswith("```"):
                break
            if re.match(r"^[-*]\s+", line):
                break
            if re.match(r"^\d+\.\s+", line):
                break
            if re.match(r"^>\s?", line):
                break
            if stripped in (r"\[", "$$"):
                break
            if parse_single_line_display_math(line):
                break
            paragraph_lines.append(line.strip())
            j += 1

        return " ".join(paragraph_lines), j

    while i < len(lines):
        line = lines[i]

        if not line.strip():
            i += 1
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading_match:
            level = len(heading_match.group(1))
            title = inline_markdown_to_html(heading_match.group(2).strip())
            blocks.append(f"<h{level}>{title}</h{level}>")
            i += 1
            continue

        single_line_math = parse_single_line_display_math(line)
        if single_line_math:
            blocks.append(single_line_math)
            i += 1
            continue

        stripped = line.strip()
        if stripped in (r"\[", "$$"):
            delimiter = stripped
            closing = r"\]" if delimiter == r"\[" else "$$"
            math_lines = []
            i += 1
            while i < len(lines) and lines[i].strip() != closing:
                math_lines.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1
            blocks.append(render_display_math(delimiter, "\n".join(math_lines)))
            continue

        if line.startswith("```"):
            fence_tokens = line[3:].strip().split()
            fence_language = fence_tokens[0].lower() if fence_tokens else ""
            safe_language = re.sub(r"[^a-z0-9_-]+", "", fence_language)
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code_lines.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1
            code_text = escape_html("\n".join(code_lines))
            if safe_language == "mermaid":
                blocks.append(f'<pre class="mermaid">{code_text}</pre>')
            elif safe_language:
                blocks.append(
                    f'<pre><code class="language-{safe_language}">{code_text}</code></pre>'
                )
            else:
                blocks.append(f"<pre><code>{code_text}</code></pre>")
            continue

        if re.match(r"^[-*]\s+", line):
            items = []
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i]):
                items.append(re.sub(r"^[-*]\s+", "", lines[i]).strip())
                i += 1
            li = "".join(f"<li>{inline_markdown_to_html(item)}</li>" for item in items)
            blocks.append(f"<ul>{li}</ul>")
            continue

        if re.match(r"^\d+\.\s+", line):
            items = []
            list_start = 1
            while i < len(lines):
                current = lines[i]
                if not current.strip():
                    # Keep ordered lists contiguous when authors place blank lines between items.
                    j = i
                    while j < len(lines) and not lines[j].strip():
                        j += 1
                    if j < len(lines) and re.match(r"^\d+\.\s+", lines[j]) and items:
                        i = j
                        continue
                    i = j
                    break

                item_match = re.match(r"^(\d+)\.\s+(.*)$", current)
                if not item_match:
                    break

                if not items:
                    list_start = int(item_match.group(1))

                item_text = item_match.group(2).strip()
                i += 1

                # Support indented continuation lines for the same ordered-list item.
                continuation = []
                while i < len(lines):
                    cont_line = lines[i]
                    if not cont_line.strip():
                        break
                    if re.match(r"^\s{2,}\S", cont_line) or cont_line.startswith("\t"):
                        continuation.append(cont_line.strip())
                        i += 1
                        continue
                    break

                if continuation:
                    item_text = item_text + " " + " ".join(continuation)

                items.append(item_text)

            li = "".join(f"<li>{inline_markdown_to_html(item)}</li>" for item in items)
            start_attr = f' start="{list_start}"' if list_start != 1 else ""
            blocks.append(f"<ol{start_attr}>{li}</ol>")
            continue

        if re.match(r"^>\s?", line):
            quote_lines = []
            while i < len(lines) and re.match(r"^>\s?", lines[i]):
                quote_lines.append(re.sub(r"^>\s?", "", lines[i]).strip())
                i += 1
            quote_text = inline_markdown_to_html(" ".join(quote_lines))
            blocks.append(f"<blockquote>{quote_text}</blockquote>")
            continue

        paragraph, next_index = collect_paragraph(i)
        if paragraph:
            blocks.append(f"<p>{inline_markdown_to_html(paragraph)}</p>")
        i = next_index

    return "\n".join(blocks)


def normalize_date(raw_value: str, fallback: str | None) -> str:
    if raw_value and re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw_value):
        return raw_value
    if fallback and re.fullmatch(r"\d{4}-\d{2}-\d{2}", fallback):
        return fallback
    return dt.date.today().isoformat()


def get_summary(meta_summary: str, markdown_body: str) -> str:
    if meta_summary:
        return meta_summary

    for line in markdown_body.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            cleaned = re.sub(r"[*`_>#-]", "", stripped)
            return cleaned[:180]

    return "New research note."


def format_date(date_string: str) -> str:
    try:
        date_obj = dt.date.fromisoformat(date_string)
    except ValueError:
        return date_string
    return date_obj.strftime("%B %d, %Y")


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
    mermaid_stylesheet = ""
    mermaid_script = ""
    if 'class="mermaid"' in body_html:
        mermaid_stylesheet = (
            '  <link rel="stylesheet" '
            'href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css" />'
        )
        mermaid_script = """  <script type=\"module\">
    import mermaid from \"https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs\";

    const diagramNodes = Array.from(document.querySelectorAll('pre.mermaid'));
    const MERMAID_COLOR_FALLBACKS = {
      '--mermaid-ch1-fill': '#e0f2fe',
      '--mermaid-ch1-stroke': '#0369a1',
      '--mermaid-ch1-text': '#0c4a6e',
      '--mermaid-ch2-fill': '#dcfce7',
      '--mermaid-ch2-stroke': '#15803d',
      '--mermaid-ch2-text': '#14532d',
      '--mermaid-ch3-fill': '#fef3c7',
      '--mermaid-ch3-stroke': '#b45309',
      '--mermaid-ch3-text': '#78350f',
      '--mermaid-ch4-fill': '#ede9fe',
      '--mermaid-ch4-stroke': '#6d28d9',
      '--mermaid-ch4-text': '#4c1d95',
      '--mermaid-ch5-fill': '#fee2e2',
      '--mermaid-ch5-stroke': '#b91c1c',
      '--mermaid-ch5-text': '#7f1d1d',
      '--mermaid-support-fill': '#f8fafc',
      '--mermaid-support-stroke': '#475569',
      '--mermaid-support-text': '#0f172a',
      '--mermaid-littlewood-fill': '#fff7ed',
      '--mermaid-littlewood-stroke': '#ea580c',
      '--mermaid-littlewood-text': '#7c2d12'
    };

    function readActiveTheme() {
      const explicitTheme = document.documentElement.getAttribute('data-theme');
      if (explicitTheme === 'light' || explicitTheme === 'dark') return explicitTheme;
      if (typeof window.matchMedia === 'function' && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        return 'dark';
      }
      return 'light';
    }

    function getMermaidTheme(theme) {
      return theme === 'dark' ? 'dark' : 'default';
    }

    function readMermaidColor(token) {
      const rootStyle = window.getComputedStyle(document.documentElement);
      const value = rootStyle.getPropertyValue(token).trim();
      return value || MERMAID_COLOR_FALLBACKS[token] || '#000000';
    }

    function resolveMermaidCssVars(sourceText) {
      let resolved = sourceText;
      Object.keys(MERMAID_COLOR_FALLBACKS).forEach(function (token) {
        const replacement = readMermaidColor(token);
        const marker = 'var(' + token + ')';
        resolved = resolved.split(marker).join(replacement);
      });
      return resolved;
    }

    async function renderMermaid(theme) {
      if (!diagramNodes.length) return;

      diagramNodes.forEach(function (node) {
        if (!node.dataset.mermaidSource) {
          node.dataset.mermaidSource = node.textContent || '';
        }

        const resolvedSource = resolveMermaidCssVars(node.dataset.mermaidSource);
        node.removeAttribute('data-processed');
        node.textContent = resolvedSource;
      });

      mermaid.initialize({
        startOnLoad: false,
        securityLevel: \"loose\",
        forceLegacyMathML: true,
        theme: getMermaidTheme(theme),
        flowchart: {
          htmlLabels: true,
        }
      });

      try {
        await mermaid.run({ nodes: diagramNodes });
      } catch (error) {}
    }

    let renderQueue = Promise.resolve();

    function queueRender(theme) {
      renderQueue = renderQueue.then(function () {
        return renderMermaid(theme);
      });
      return renderQueue;
    }

    function getRevealAncestors() {
      const ancestors = new Set();
      diagramNodes.forEach(function (node) {
        let current = node.parentElement;
        while (current) {
          if (current.classList && current.classList.contains('reveal-up')) {
            ancestors.add(current);
          }
          current = current.parentElement;
        }
      });
      return Array.from(ancestors);
    }

    function waitForRevealAnimations() {
      const revealAncestors = getRevealAncestors();
      if (!revealAncestors.length) return Promise.resolve();

      const waits = revealAncestors.map(function (element) {
        const style = window.getComputedStyle(element);
        const duration = parseFloat(style.animationDuration || '0') || 0;
        const delay = parseFloat(style.animationDelay || '0') || 0;
        const totalMs = Math.round((duration + delay) * 1000);

        if (style.animationName === 'none' || totalMs <= 0) {
          return Promise.resolve();
        }

        return new Promise(function (resolve) {
          let done = false;
          function finish() {
            if (done) return;
            done = true;
            element.removeEventListener('animationend', onAnimationEnd);
            resolve();
          }
          function onAnimationEnd(event) {
            if (event.target === element) finish();
          }
          element.addEventListener('animationend', onAnimationEnd);
          window.setTimeout(finish, Math.max(totalMs + 120, 700));
        });
      });

      return Promise.all(waits).then(function () {});
    }

    waitForRevealAnimations().then(function () {
      queueRender(readActiveTheme());
    });

    window.addEventListener('themechange', function (event) {
      const detailTheme = event && event.detail ? event.detail.theme : '';
      const nextTheme = detailTheme === 'light' || detailTheme === 'dark'
        ? detailTheme
        : readActiveTheme();
      queueRender(nextTheme);
    });
  </script>
"""

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

    teaching_dropdown = render_nav_dropdown(
        "Teaching",
        teaching_dropdown_items,
    )
    blog_dropdown = render_nav_dropdown(
        "Blog",
        blog_dropdown_items,
        active=True,
        active_href=f"./{str(post['slug']).strip()}.html",
    )

    return f"""<!DOCTYPE html>
<html lang=\"en\" data-ga-id=\"{escape_html(ga_id)}\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{escape_html(post['title'])} | Wei You</title>
  <meta name=\"description\" content=\"{escape_html(post['summary'])}\" />
  <link rel=\"preconnect\" href=\"https://fonts.googleapis.com\" />
  <link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin />
  <link href=\"https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&amp;family=Space+Grotesk:wght@400;500;600;700&amp;display=swap\" rel=\"stylesheet\" />
  <script>
    (function () {{
      try {{
        var storedTheme = localStorage.getItem('wy-theme');
        var themeSource = localStorage.getItem('wy-theme-source');
        if (themeSource === 'manual' && (storedTheme === 'light' || storedTheme === 'dark')) {{
          document.documentElement.setAttribute('data-theme', storedTheme);
        }}
      }} catch (error) {{}}
    }})();
  </script>
  <link rel=\"stylesheet\" href=\"../css/site.css\" />
{mermaid_stylesheet}
</head>
<body>
  <header class=\"site-header\" id=\"top\">
    <div class=\"container nav-wrap\">
      <a class=\"brand\" href=\"../index.html#home\">Wei You</a>
      <div class=\"nav-controls\">
        <button class=\"theme-toggle\" type=\"button\" aria-label=\"Toggle theme\" aria-pressed=\"false\">
          <span class=\"theme-toggle__text\">Dark</span>
        </button>
        <button class=\"menu-toggle\" type=\"button\" aria-label=\"Open menu\" aria-controls=\"site-nav\" aria-expanded=\"false\">
          <span></span>
          <span></span>
        </button>
        <nav class=\"site-nav\" id=\"site-nav\" aria-label=\"Primary\">
          <a class=\"nav-link\" href=\"../index.html#home\">Home</a>
          <a class=\"nav-link\" href=\"../index.html#research\">Research</a>
          <a class=\"nav-link\" href=\"../index.html#talks\">Talks</a>
{indent_block(teaching_dropdown, '          ')}
          <a class=\"nav-link\" href=\"../index.html#team\">Team</a>
          <a class=\"nav-link\" href=\"../index.html#about\">About</a>
{indent_block(blog_dropdown, '          ')}
        </nav>
      </div>
    </div>
  </header>

  <main class=\"teaching-page\">
    <section class=\"container teaching-shell\">
      <header class=\"course-hero reveal-up\">
        <p class=\"eyebrow\">Research Notes</p>
        <h1>{escape_html(post['title'])}</h1>
        <p class=\"blog-meta\"><time datetime=\"{post['date']}\">{format_date(post['date'])}</time>{tags_markup}</p>
        <p class=\"course-lead\">{escape_html(post['summary'])}</p>
      </header>

      <section class=\"module-section reveal-up delay-1\">
        <article class=\"panel post-card\">
          <div class=\"post-body\">
{body_html}
          </div>
        </article>
      </section>

      <div class=\"hero-links reveal-up delay-2\">
        <a class=\"chip\" href=\"./index.html\">All posts</a>
        <a class=\"chip\" href=\"../index.html#blog\">Back to main site</a>
      </div>
    </section>
  </main>

  <footer class=\"site-footer\">
    <div class=\"container footer-inner\">
      <p>&copy; <span id=\"year\"></span> Wei You</p>
      <p>Department of Industrial Engineering and Decision Analytics, HKUST</p>
    </div>
  </footer>

  <button class=\"back-to-top\" type=\"button\" aria-label=\"Back to top\">Top</button>
  <script>
    window.MathJax = {{
      tex: {{
        inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
        displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
        processEscapes: true
      }},
      chtml: {{
        mtextInheritFont: true,
        merrorInheritFont: true
      }},
      options: {{
        skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code']
      }}
    }};
  </script>
  <script defer src=\"https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js\"></script>
{mermaid_script}  <script src=\"../js/site.js\" defer></script>
  <script>
    const yearNode = document.getElementById(\"year\");
    if (yearNode) yearNode.textContent = String(new Date().getFullYear());
  </script>
</body>
</html>
"""


def blog_index_template(
    posts: list[dict[str, object]],
    ga_id: str,
    published_courses: list[dict[str, str]],
) -> str:
    cards = []

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

    teaching_dropdown = render_nav_dropdown(
        "Teaching",
        teaching_dropdown_items,
    )
    blog_dropdown = render_nav_dropdown(
        "Blog",
        blog_dropdown_items,
        active=True,
        active_href="./index.html",
    )

    return f"""<!DOCTYPE html>
<html lang=\"en\" data-ga-id=\"{escape_html(ga_id)}\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Blog | Wei You</title>
  <meta name=\"description\" content=\"Research notes and updates by Wei You.\" />
  <link rel=\"preconnect\" href=\"https://fonts.googleapis.com\" />
  <link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin />
  <link href=\"https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&amp;family=Space+Grotesk:wght@400;500;600;700&amp;display=swap\" rel=\"stylesheet\" />
  <script>
    (function () {{
      try {{
        var storedTheme = localStorage.getItem('wy-theme');
        var themeSource = localStorage.getItem('wy-theme-source');
        if (themeSource === 'manual' && (storedTheme === 'light' || storedTheme === 'dark')) {{
          document.documentElement.setAttribute('data-theme', storedTheme);
        }}
      }} catch (error) {{}}
    }})();
  </script>
  <link rel=\"stylesheet\" href=\"../css/site.css\" />
</head>
<body>
  <header class=\"site-header\" id=\"top\">
    <div class=\"container nav-wrap\">
      <a class=\"brand\" href=\"../index.html#home\">Wei You</a>
      <div class=\"nav-controls\">
        <button class=\"theme-toggle\" type=\"button\" aria-label=\"Toggle theme\" aria-pressed=\"false\">
          <span class=\"theme-toggle__text\">Dark</span>
        </button>
        <button class=\"menu-toggle\" type=\"button\" aria-label=\"Open menu\" aria-controls=\"site-nav\" aria-expanded=\"false\">
          <span></span>
          <span></span>
        </button>
        <nav class=\"site-nav\" id=\"site-nav\" aria-label=\"Primary\">
          <a class=\"nav-link\" href=\"../index.html#home\">Home</a>
          <a class=\"nav-link\" href=\"../index.html#research\">Research</a>
          <a class=\"nav-link\" href=\"../index.html#talks\">Talks</a>
{indent_block(teaching_dropdown, '          ')}
          <a class=\"nav-link\" href=\"../index.html#team\">Team</a>
          <a class=\"nav-link\" href=\"../index.html#about\">About</a>
{indent_block(blog_dropdown, '          ')}
        </nav>
      </div>
    </div>
  </header>

  <main class=\"teaching-page\">
    <section class=\"container teaching-shell\">
      <header class=\"course-hero reveal-up\">
        <p class=\"eyebrow\">Writing</p>
        <h1>Blog</h1>
        <p class=\"course-lead\">Research notes, teaching reflections, and short updates.</p>
      </header>

      <section class=\"module-section reveal-up delay-1\">
        <div class=\"module-grid\">
{card_markup}
        </div>
      </section>

      <div class=\"hero-links reveal-up delay-2\">
        <a class=\"chip\" href=\"../index.html#blog\">Back to main site</a>
      </div>
    </section>
  </main>

  <footer class=\"site-footer\">
    <div class=\"container footer-inner\">
      <p>&copy; <span id=\"year\"></span> Wei You</p>
      <p>Department of Industrial Engineering and Decision Analytics, HKUST</p>
    </div>
  </footer>

  <button class=\"back-to-top\" type=\"button\" aria-label=\"Back to top\">Top</button>
  <script>
    window.MathJax = {{
      tex: {{
        inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
        displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
        processEscapes: true
      }},
      chtml: {{
        mtextInheritFont: true,
        merrorInheritFont: true
      }},
      options: {{
        skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code']
      }}
    }};
  </script>
  <script defer src=\"https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js\"></script>
  <script src=\"../js/site.js\" defer></script>
  <script>
    const yearNode = document.getElementById(\"year\");
    if (yearNode) yearNode.textContent = String(new Date().getFullYear());
  </script>
</body>
</html>
"""


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
        html_body = markdown_to_html(body)

        posts.append(
            {
                "title": title,
                "slug": slug,
                "date": date,
                "summary": summary,
                "tags": tags,
                "html": html_body,
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


# ---------------------------------------------------------------------------
# Research build
# ---------------------------------------------------------------------------

def join_authors(authors: list[str]) -> str:
    if not authors:
        return ""
    if len(authors) == 1:
        return authors[0]
    if len(authors) == 2:
        return f"{authors[0]} and {authors[1]}"
    return ", ".join(authors[:-1]) + ", and " + authors[-1]


def emphasize_authors(authors: list[str], highlighted: set[str]) -> str:
    rendered = []
    for author in authors:
        safe_name = escape_html(author)
        if author in highlighted:
            rendered.append(f"<strong>{safe_name}</strong>")
        else:
            rendered.append(safe_name)
    return join_authors(rendered)


def render_links(links: list[dict[str, str]]) -> str:
    if not links:
        return ""

    rendered = []
    for link in links:
        label = escape_html(str(link["label"]))
        url = escape_html(str(link["url"]))
        rendered.append(
            f'<a href="{url}" target="_blank" rel="noopener noreferrer">{label}</a>'
        )

    return "<div class=\"paper-links\">" + "".join(rendered) + "</div>"


def render_abstract(abstract: str) -> str:
    parts = [part.strip() for part in abstract.split("\n\n") if part.strip()]
    if not parts:
        return ""

    paragraphs = "".join(f"<p>{escape_html(part)}</p>" for part in parts)
    return f"<div class=\"paper-abstract\" hidden>{paragraphs}</div>"


def topic_sort_key(paper: dict[str, object]) -> str:
    topic = str(paper.get("topic", "")).strip()
    if topic:
        return topic
    if str(paper.get("section", "")).strip() == "working":
        return "Working Papers"
    return "Other"


def render_paper(paper: dict[str, object], highlighted: set[str]) -> str:
    paper_type = str(paper["type"])
    badge = escape_html(BADGE_LABELS.get(paper_type, paper_type.title()))
    year = int(paper["year"])
    topic_key = escape_html(topic_sort_key(paper))

    title = escape_html(str(paper["title"]))

    authors = [str(author) for author in paper["authors"]]
    authors_html = emphasize_authors(authors, highlighted)

    note = str(paper.get("note", "")).strip()
    if note:
        meta_html = f"<p class=\"paper-meta\">{authors_html}, {escape_html(note)}</p>"
    else:
        meta_html = f"<p class=\"paper-meta\">{authors_html}</p>"

    venue = str(paper.get("venue", "")).strip()
    venue_html = (
        f"<p class=\"paper-venue\"><em>{escape_html(venue)}</em></p>"
        if venue
        else ""
    )

    links = paper.get("links", [])
    links_html = render_links(links if isinstance(links, list) else [])

    abstract = str(paper.get("abstract", "")).strip()
    has_abstract = bool(abstract)
    abstract_html = render_abstract(abstract)

    paper_class = "paper paper-collapsible" if has_abstract else "paper"
    interactive_attrs = (
        ' tabindex="0" role="button" aria-expanded="false"'
        if has_abstract
        else ""
    )

    return "\n".join(
        [
            (
                f'<article class="{paper_class}" data-type="{escape_html(paper_type)}" '
                f'data-year="{year}" data-topic="{topic_key}"{interactive_attrs}>'
            ),
            "  <div class=\"paper-header\">",
            f"    <span class=\"paper-year\">{year}</span>",
            f"    <span class=\"badge {escape_html(paper_type)}\">{badge}</span>",
            "  </div>",
            f"  <h4 class=\"paper-title\">{title}</h4>",
            f"  {meta_html}",
            f"  {venue_html}" if venue_html else "",
            f"  {links_html}" if links_html else "",
            f"  {abstract_html}",
            "</article>",
        ]
    )


def sort_section(papers: list[dict[str, object]]) -> list[dict[str, object]]:
    indexed = [(idx, paper) for idx, paper in enumerate(papers)]
    indexed.sort(key=lambda item: (-int(item[1]["year"]), item[0]))
    return [paper for _, paper in indexed]


def render_section(
    section_key: str,
    heading: str,
    animation_class: str,
    papers: list[dict[str, object]],
    highlighted: set[str],
) -> str:
    cards = "\n\n".join(render_paper(paper, highlighted) for paper in papers)

    return "\n".join(
        [
            f'<div data-paper-section="{section_key}" class="{animation_class}">',
            f"  <h3 class=\"subsection-title\">{heading}</h3>",
            "  <div class=\"paper-list\">",
            cards,
            "  </div>",
            "</div>",
        ]
    )


def validate_paper(paper: dict[str, object]) -> None:
    required_fields = [
        "id",
        "section",
        "type",
        "year",
        "title",
        "topic",
        "authors",
        "abstract",
        "links",
    ]
    missing = [field for field in required_fields if field not in paper]
    if missing:
        raise ValueError(f"Paper entry missing fields {missing}: {paper}")

    if paper["section"] not in {"working", "publication"}:
        raise ValueError(f"Invalid section in paper {paper['id']}: {paper['section']}")

    if paper["type"] not in {"working", "journal", "conference", "thesis"}:
        raise ValueError(f"Invalid type in paper {paper['id']}: {paper['type']}")

    if not isinstance(paper["authors"], list) or not paper["authors"]:
        raise ValueError(f"authors must be a non-empty list in paper {paper['id']}")

    if not isinstance(paper["links"], list):
        raise ValueError(f"links must be a list in paper {paper['id']}")

    if "selected" in paper and not isinstance(paper["selected"], bool):
        raise ValueError(f"selected must be a boolean in paper {paper['id']}")


def load_research_data() -> tuple[list[dict[str, object]], set[str]]:
    payload = json.loads(RESEARCH_DATA_PATH.read_text(encoding="utf-8"))

    papers = payload.get("papers", [])
    if not isinstance(papers, list):
        raise ValueError("`papers` must be a list in content/research/papers.json")

    highlight_authors = payload.get("highlight_authors", [])
    if not isinstance(highlight_authors, list):
        raise ValueError("`highlight_authors` must be a list")

    for paper in papers:
        if not isinstance(paper, dict):
            raise ValueError(f"Each paper must be an object, got: {paper}")
        validate_paper(paper)

    return papers, set(str(name) for name in highlight_authors)


def indent_block(block: str, indent: str) -> str:
    return "\n".join((indent + line if line else "") for line in block.splitlines())


def build_research_markup(papers: list[dict[str, object]], highlighted: set[str]) -> str:
    working = sort_section([p for p in papers if p["section"] == "working"])
    publications = sort_section([p for p in papers if p["section"] == "publication"])

    working_markup = render_section(
        section_key="working",
        heading="Working Papers",
        animation_class="reveal-up delay-2",
        papers=working,
        highlighted=highlighted,
    )

    publication_markup = render_section(
        section_key="pub",
        heading="Publications",
        animation_class="reveal-up delay-3",
        papers=publications,
        highlighted=highlighted,
    )

    return working_markup + "\n\n" + publication_markup


def update_index_block(start_marker: str, end_marker: str, markup: str) -> None:
    html_text = INDEX_PATH.read_text(encoding="utf-8")

    pattern = re.compile(
        rf"^(?P<indent>[ \t]*){re.escape(start_marker)}\n(?P<body>.*?)(?P=indent){re.escape(end_marker)}",
        re.DOTALL | re.MULTILINE,
    )
    match = pattern.search(html_text)
    if not match:
        raise ValueError(f"Markers {start_marker} / {end_marker} were not found in index.html")

    indent = match.group("indent")
    replacement = (
        f"{indent}{start_marker}\n"
        f"{indent_block(markup, indent)}\n"
        f"{indent}{end_marker}"
    )

    updated_html = html_text[: match.start()] + replacement + html_text[match.end() :]
    INDEX_PATH.write_text(updated_html, encoding="utf-8")


def preferred_selected_link(paper: dict[str, object]) -> str | None:
    links = paper.get("links", [])
    if not isinstance(links, list) or not links:
        return None

    preferred_labels = ["journal", "preprint", "arxiv", "pdf"]
    for preferred in preferred_labels:
        for link in links:
            label = str(link.get("label", "")).strip().lower()
            url = str(link.get("url", "")).strip()
            if label == preferred and url:
                return url

    for link in links:
        url = str(link.get("url", "")).strip()
        if url:
            return url

    return None


def build_selected_papers_markup(papers: list[dict[str, object]]) -> str:
    indexed = [(idx, paper) for idx, paper in enumerate(papers)]
    selected = [item for item in indexed if bool(item[1].get("selected", False))]
    selected.sort(key=lambda item: (-int(item[1]["year"]), item[0]))

    if not selected:
        return "<ul class=\"simple-list\"><li><span class=\"paper-year\">-</span> No selected papers tagged yet.</li></ul>"

    lines = ["<ul class=\"simple-list\">"]
    for _, paper in selected:
        year = int(paper["year"])
        title = escape_html(str(paper["title"]))
        url = preferred_selected_link(paper)

        if url:
            safe_url = escape_html(url)
            lines.append(
                f'  <li><span class="paper-year">{year}</span> <a href="{safe_url}" target="_blank" rel="noopener noreferrer">{title}</a></li>'
            )
        else:
            lines.append(f'  <li><span class="paper-year">{year}</span> {title}</li>')

    lines.append("</ul>")
    return "\n".join(lines)


def build_research() -> int:
    papers, highlighted = load_research_data()
    selected_markup = build_selected_papers_markup(papers)
    markup = build_research_markup(papers, highlighted)
    update_index_block(SELECTED_START_MARKER, SELECTED_END_MARKER, selected_markup)
    update_index_block(RESEARCH_START_MARKER, RESEARCH_END_MARKER, markup)

    print(f"Built research section from {len(papers)} entries.")
    print("Updated: selected papers on home section.")
    print("Updated: index.html")
    return len(papers)


# ---------------------------------------------------------------------------
# Teaching build
# ---------------------------------------------------------------------------

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

    return f"""<!DOCTYPE html>
<html lang="en" data-ga-id="{escape_html(ga_id)}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Teaching | Wei You</title>
  <meta name="description" content="Course pages and teaching materials by Wei You." />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&amp;family=Space+Grotesk:wght@400;500;600;700&amp;family=Noto+Sans+SC:wght@400;500;700&amp;display=swap" rel="stylesheet" />
  <script>
    (function () {{
      try {{
        var storedTheme = localStorage.getItem('wy-theme');
        var themeSource = localStorage.getItem('wy-theme-source');
        if (themeSource === 'manual' && (storedTheme === 'light' || storedTheme === 'dark')) {{
          document.documentElement.setAttribute('data-theme', storedTheme);
        }}
      }} catch (error) {{}}
    }})();
  </script>
  <link rel="stylesheet" href="../css/site.css" />
</head>
<body>
  <header class="site-header" id="top">
    <div class="container nav-wrap">
      <a class="brand" href="../index.html#home">Wei You</a>
      <div class="nav-controls">
        <button class="theme-toggle" type="button" aria-label="Toggle theme" aria-pressed="false">
          <span class="theme-toggle__text">Dark</span>
        </button>
        <button class="menu-toggle" type="button" aria-label="Open menu" aria-controls="site-nav" aria-expanded="false">
          <span></span>
          <span></span>
        </button>
        <nav class="site-nav" id="site-nav" aria-label="Primary">
          <a class="nav-link" href="../index.html#home">Home</a>
          <a class="nav-link" href="../index.html#research">Research</a>
          <a class="nav-link" href="../index.html#talks">Talks</a>
{indent_block(teaching_dropdown, '          ')}
          <a class="nav-link" href="../index.html#team">Team</a>
          <a class="nav-link" href="../index.html#about">About</a>
{indent_block(blog_dropdown, '          ')}
        </nav>
      </div>
    </div>
  </header>

  <main class="teaching-page">
    <section class="container teaching-shell">
      <header class="course-hero reveal-up">
        <p class="eyebrow">Courses</p>
        <h1>Teaching</h1>
      </header>

      <section class="module-section reveal-up delay-1">
        <div class="module-grid">
{cards_html}
        </div>
      </section>
    </section>
  </main>

  <footer class="site-footer">
    <div class="container footer-inner">
      <p>&copy; <span id="year"></span> Wei You</p>
      <p>Department of Industrial Engineering and Decision Analytics, HKUST</p>
    </div>
  </footer>

  <button class="back-to-top" type="button" aria-label="Back to top">Top</button>
  <script src="../js/site.js" defer></script>
  <script>
    const yearNode = document.getElementById("year");
    if (yearNode) yearNode.textContent = String(new Date().getFullYear());
  </script>
</body>
</html>
"""


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

    return f"""<!DOCTYPE html>
<html lang="en" data-ga-id="{escape_html(ga_id)}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{code} {title} | Teaching</title>
  <meta name="description" content="{summary}" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&amp;family=Space+Grotesk:wght@400;500;600;700&amp;family=Noto+Sans+SC:wght@400;500;700&amp;display=swap" rel="stylesheet" />
  <script>
    (function () {{
      try {{
        var storedTheme = localStorage.getItem('wy-theme');
        var themeSource = localStorage.getItem('wy-theme-source');
        if (themeSource === 'manual' && (storedTheme === 'light' || storedTheme === 'dark')) {{
          document.documentElement.setAttribute('data-theme', storedTheme);
        }}
      }} catch (error) {{}}
    }})();
  </script>
  <link rel="stylesheet" href="../css/site.css" />
</head>
<body>
  <header class="site-header" id="top">
    <div class="container nav-wrap">
      <a class="brand" href="../index.html#home">Wei You</a>
      <div class="nav-controls">
        <button class="theme-toggle" type="button" aria-label="Toggle theme" aria-pressed="false">
          <span class="theme-toggle__text">Dark</span>
        </button>
        <button class="menu-toggle" type="button" aria-label="Open menu" aria-controls="site-nav" aria-expanded="false">
          <span></span>
          <span></span>
        </button>
        <nav class="site-nav" id="site-nav" aria-label="Primary">
          <a class="nav-link" href="../index.html#home">Home</a>
          <a class="nav-link" href="../index.html#research">Research</a>
          <a class="nav-link" href="../index.html#talks">Talks</a>
{indent_block(teaching_dropdown, '          ')}
          <a class="nav-link" href="../index.html#team">Team</a>
          <a class="nav-link" href="../index.html#about">About</a>
{indent_block(blog_dropdown, '          ')}
        </nav>
      </div>
    </div>
  </header>

  <main class="teaching-page">
    <section class="container teaching-shell">
      <header class="course-hero reveal-up">
        <p class="eyebrow">HKUST IEDA</p>
        <h1>{code}: {title}</h1>
        <p class="course-lead">{overview}</p>
        <div class="hero-links">
          <a class="chip" href="./index.html">All Course Pages</a>
          <a class="chip" href="../index.html#teaching">Main Site Teaching Section</a>
        </div>
      </header>

      <section class="course-snapshot reveal-up delay-1" aria-label="Course snapshot">
        <article class="panel">
          <h2>Course Snapshot</h2>
          <ul class="stack-list">
            <li><strong>Period:</strong> {period}</li>
            <li><strong>Audience:</strong> {audience}</li>
            <li><strong>Prerequisites:</strong> {prerequisites}</li>
          </ul>
        </article>
        <article class="panel">
          <h2>Learning Outcomes</h2>
          <ul class="stack-list">
            {outcomes_items}
          </ul>
        </article>
      </section>

      <section class="module-section reveal-up delay-2" aria-label="Lecture modules">
        <header class="section-header">
          <p class="eyebrow">Lecture Modules</p>
          <h2>Materials</h2>
        </header>
        <div class="module-grid">
          {modules_html}
        </div>
      </section>
    </section>
  </main>

  <footer class="site-footer">
    <div class="container footer-inner">
      <p>&copy; <span id="year"></span> Wei You</p>
      <p>Department of Industrial Engineering and Decision Analytics, HKUST</p>
    </div>
  </footer>

  <button class="back-to-top" type="button" aria-label="Back to top">Top</button>
  <script src="../js/site.js" defer></script>
  <script>
    const yearNode = document.getElementById("year");
    if (yearNode) yearNode.textContent = String(new Date().getFullYear());
  </script>
</body>
</html>
"""


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


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main() -> None:
    print("[1/3] Building research section...")
    build_research()
    posts = read_source_posts()
    courses = load_teaching_data()
    recent_posts = recent_posts_for_nav(posts)
    print("[2/3] Building blog...")
    build_blog(posts, courses)
    print("[3/3] Building teaching pages...")
    build_teaching(courses, recent_posts)
    update_index_nav_dropdowns(posts, courses)
    print("Updated: index navigation dropdowns.")
    print("Site build complete.")


if __name__ == "__main__":
    main()
