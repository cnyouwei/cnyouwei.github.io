"""Post-build sanity checks: did every piece of data make it into the output?

Cheap, dependency-free verification run at the end of every build, so a broken
template or a renamed asset fails the build instead of shipping.
"""

from __future__ import annotations

import html
import re

from markupsafe import escape as jinja_escape

from .config import DIST_DIR
from .data import SiteData

_HREF = re.compile(r"""(?:href|src)=["']([^"'#]+)["']""")


class CheckError(Exception):
    pass


def _fail(problems: list[str]) -> None:
    if problems:
        bullet_list = "\n".join(f"  - {p}" for p in problems)
        raise CheckError(f"Build verification failed:\n{bullet_list}")


def check_site(data: SiteData) -> None:
    problems: list[str] = []

    index = DIST_DIR / "index.html"
    if not index.exists():
        _fail(["dist/index.html was not generated"])
    index_html = index.read_text(encoding="utf-8")

    # Every paper title must appear on the home page. Compare using the same
    # escaping Jinja autoescape uses (html.escape produces different entities
    # for quotes, e.g. &#x27; vs &#39;, which caused spurious failures).
    for paper in data.papers:
        if str(jinja_escape(paper["title"])) not in index_html:
            problems.append(f"paper missing from home page: {paper['id']}")

    # Every post page and published course page must exist.
    for post in data.posts:
        if not (DIST_DIR / "blogs" / f"{post['slug']}.html").exists():
            problems.append(f"blog page missing: blogs/{post['slug']}.html")
    for course in data.teaching["courses"]:
        if course.get("published") and not (
            DIST_DIR / "teaching" / f"{course['slug']}.html"
        ).exists():
            problems.append(f"course page missing: teaching/{course['slug']}.html")

    # Every local href/src in generated HTML must resolve inside dist/.
    for page in DIST_DIR.rglob("*.html"):
        rel_dir = page.parent
        for url in _HREF.findall(page.read_text(encoding="utf-8")):
            if url.startswith(("http://", "https://", "mailto:", "data:")):
                continue
            url = html.unescape(url).split("?")[0]
            target = (rel_dir / url).resolve()
            if not target.exists():
                problems.append(f"{page.relative_to(DIST_DIR)}: broken local link {url}")

    _fail(problems)
    print(f"Site checks passed ({len(data.papers)} papers, {len(data.posts)} posts).")
