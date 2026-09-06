"""Post-build sanity checks: did every piece of data make it into the output?

Cheap, dependency-free verification run at the end of every build, so a broken
template or a renamed asset fails the build instead of shipping.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree

from markupsafe import escape as jinja_escape

from .config import (
    BADGE_LABELS,
    DIST_DIR,
    VENUE_TIER_LABELS,
    venue_metadata,
    venue_tier,
    paper_citation,
)
from .data import SiteData
from .site import page_registry
from .validation import DataError, local_target, url_value


class Document(HTMLParser):
    """Collect actual HTML attributes instead of interpreting HTML with regexes."""

    def __init__(self, source: str) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.duplicate_ids: set[str] = set()
        self.urls: list[str] = []
        self.problems: list[str] = []
        self.h1_count = 0
        self.canonicals: list[str] = []
        self.meta: dict[str, str] = {}
        self.title = ""
        self._in_title = False
        self.feed(source)
        self.close()

    def handle_starttag(self, tag, attrs) -> None:
        attributes = dict(attrs)
        element_id = attributes.get("id")
        if element_id:
            if element_id in self.ids:
                self.duplicate_ids.add(element_id)
            self.ids.add(element_id)
        for name, value in attrs:
            if name in ("href", "src", "poster") and value is not None:
                self.urls.append(value)
            if name.startswith("on") or name == "srcdoc":
                self.problems.append(f"unsafe inline HTML attribute: {name}")
        if tag == "h1":
            self.h1_count += 1
        elif tag == "title":
            self._in_title = True
        elif tag == "link" and "canonical" in (attributes.get("rel") or "").split():
            self.canonicals.append(attributes.get("href") or "")
        elif tag == "meta":
            key = attributes.get("name") or attributes.get("property")
            if key:
                self.meta[key] = attributes.get("content") or ""
            if (attributes.get("http-equiv") or "").lower() == "refresh":
                content = attributes.get("content") or ""
                marker = content.lower().find("url=")
                if marker >= 0:
                    destination = content[marker + 4:].strip().strip("\"'")
                    self.urls.append(destination)

    def handle_endtag(self, tag) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, value) -> None:
        if self._in_title:
            self.title += value


def check_links(root: Path, documents: dict[Path, Document], site_url: str = "") -> list[str]:
    root = root.resolve()
    problems = []
    origin = urlsplit(site_url)
    for page, document in documents.items():
        prefix = str(page.relative_to(root))
        for detail in document.problems:
            problems.append(f"{prefix}: {detail}")
        for element_id in sorted(document.duplicate_ids):
            problems.append(f"{prefix}: duplicate id '{element_id}'")
        for url in document.urls:
            try:
                parsed = url_value(url, prefix)
                if parsed.scheme and not (parsed.scheme == origin.scheme and parsed.netloc == origin.netloc):
                    continue
                if not parsed.path:
                    target = page.resolve()
                else:
                    target = local_target(root, parsed.path, relative_to=page.parent)
                if target.is_dir():
                    target = target / "index.html"
                if not target.is_file():
                    raise DataError(f"broken local link {url}")
                fragment = unquote(parsed.fragment).split(":~:text=", 1)[0]
                if fragment and target.suffix.lower() == ".html":
                    destination = documents.get(target)
                    if destination is None:
                        destination = Document(target.read_text(encoding="utf-8"))
                    if fragment not in destination.ids:
                        raise DataError(f"missing fragment '{fragment}' in {url}")
            except DataError as exc:
                problems.append(f"{prefix}: {exc}")
    return problems


@dataclass
class _Badge:
    classes: set[str]
    title: str
    text: list[str] = field(default_factory=list)
    depth: int = 1


@dataclass
class _PaperCard:
    paper_id: str
    data_type: str
    search_text: str
    badges: list[_Badge] = field(default_factory=list)
    citation_text: list[str] = field(default_factory=list)
    citation_count: int = 0
    depth: int = 1


class _PaperCardParser(HTMLParser):
    """Collect the semantic badge markup from each generated paper card."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.cards: dict[str, list[_PaperCard]] = {}
        self._card: _PaperCard | None = None
        self._badge: _Badge | None = None
        self._citation_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if self._card is None:
            element_id = attributes.get("id") or ""
            if tag == "article" and element_id.startswith("paper-"):
                self._card = _PaperCard(
                    paper_id=element_id.removeprefix("paper-"),
                    data_type=attributes.get("data-type") or "",
                    search_text=attributes.get("data-search") or "",
                )
            return

        if tag == "article":
            self._card.depth += 1

        if self._badge is not None:
            self._badge.depth += 1
            return
        if self._citation_depth:
            self._citation_depth += 1
            return

        classes = set((attributes.get("class") or "").split())
        if tag == "span" and classes.intersection(
            {"paper-type-badge", "paper-venue-badge"}
        ):
            self._badge = _Badge(classes=classes, title=attributes.get("title") or "")
        elif tag == "p" and "paper-venue" in classes:
            self._card.citation_count += 1
            self._citation_depth = 1

    def handle_endtag(self, tag: str) -> None:
        if self._card is None:
            return

        if self._badge is not None:
            self._badge.depth -= 1
            if self._badge.depth == 0:
                self._card.badges.append(self._badge)
                self._badge = None
        elif self._citation_depth:
            self._citation_depth -= 1

        if tag == "article":
            self._card.depth -= 1
            if self._card.depth == 0:
                self.cards.setdefault(self._card.paper_id, []).append(self._card)
                self._card = None
                self._badge = None
                self._citation_depth = 0

    def handle_data(self, data: str) -> None:
        if self._badge is not None:
            self._badge.text.append(data)
        elif self._card is not None and self._citation_depth:
            self._card.citation_text.append(data)


def _badge_text(badge: _Badge) -> str:
    return " ".join("".join(badge.text).split())


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
    parser = _PaperCardParser()
    parser.feed(index_html)
    parser.close()
    paper_cards = parser.cards
    expected_paper_ids = {paper["id"] for paper in data.papers}

    site_css = DIST_DIR / "css" / "site.css"
    if not site_css.exists():
        problems.append("dist/css/site.css was not generated")
    else:
        css_text = site_css.read_text(encoding="utf-8")
        for tier in VENUE_TIER_LABELS:
            selector = f".badge--venue-{tier}"
            if selector not in css_text:
                problems.append(f"venue tier CSS missing selector: {selector}")

    for paper_id in sorted(set(paper_cards) - expected_paper_ids):
        problems.append(f"unexpected paper card on home page: {paper_id}")

    # Every paper title must appear on the home page. Compare using the same
    # escaping Jinja autoescape uses (html.escape produces different entities
    # for quotes, e.g. &#x27; vs &#39;, which caused spurious failures).
    for paper in data.papers:
        if str(jinja_escape(paper["title"])) not in index_html:
            problems.append(f"paper missing from home page: {paper['id']}")

        cards = paper_cards.get(paper["id"], [])
        if len(cards) != 1:
            problems.append(
                f"paper card missing or duplicated: {paper['id']} (found {len(cards)})"
            )
            continue

        card = cards[0]
        if card.data_type != paper["type"]:
            problems.append(
                f"paper {paper['id']}: expected data-type '{paper['type']}', "
                f"got '{card.data_type}'"
            )

        venue_name = paper.get("venue")
        metadata = venue_metadata(venue_name) if venue_name else None
        search_terms = [venue_name, metadata.abbreviation] if metadata else []
        if paper.get("venue_display"):
            search_terms.append(paper["venue_display"])
        for search_term in search_terms:
            if search_term.casefold() not in card.search_text.casefold():
                problems.append(
                    f"paper {paper['id']}: data-search missing venue term "
                    f"'{search_term}'"
                )

        expected_citation = paper_citation(paper)
        expected_citation_count = 1 if expected_citation else 0
        actual_citation = " ".join("".join(card.citation_text).split())
        if card.citation_count != expected_citation_count:
            problems.append(
                f"paper {paper['id']}: expected {expected_citation_count} venue "
                f"citation(s), "
                f"found {card.citation_count}"
            )
        elif expected_citation and actual_citation != expected_citation:
            problems.append(
                f"paper {paper['id']}: expected citation '{expected_citation}', "
                f"got '{actual_citation}'"
            )

        type_badges = [b for b in card.badges if "paper-type-badge" in b.classes]
        if len(type_badges) != 1:
            problems.append(
                f"paper {paper['id']}: expected one type badge, found {len(type_badges)}"
            )
        else:
            type_badge = type_badges[0]
            expected_type = BADGE_LABELS[paper["type"]]
            actual_type = _badge_text(type_badge)
            if actual_type != expected_type:
                problems.append(
                    f"paper {paper['id']}: expected type badge '{expected_type}', "
                    f"got '{actual_type}'"
                )
            expected_class = f"badge--{paper['type']}"
            type_modifier_classes = {
                class_name
                for class_name in type_badge.classes
                if class_name.startswith("badge--")
            }
            if (
                "badge" not in type_badge.classes
                or type_modifier_classes != {expected_class}
            ):
                problems.append(
                    f"paper {paper['id']}: expected only type class "
                    f"'{expected_class}', got {sorted(type_modifier_classes)}"
                )

        venue_badges = [b for b in card.badges if "paper-venue-badge" in b.classes]
        expected_venue_badge_count = 1 if metadata else 0
        if len(venue_badges) != expected_venue_badge_count:
            problems.append(
                f"paper {paper['id']}: expected {expected_venue_badge_count} venue "
                f"badge(s), found {len(venue_badges)}"
            )
        elif metadata is not None:
            venue_badge = venue_badges[0]
            expected_venue = metadata.abbreviation
            actual_venue = _badge_text(venue_badge)
            if actual_venue != expected_venue:
                problems.append(
                    f"paper {paper['id']}: expected venue badge '{expected_venue}', "
                    f"got '{actual_venue}'"
                )
            expected_tier = venue_tier(venue_name)
            expected_tier_class = f"badge--venue-{expected_tier}"
            tier_modifier_classes = {
                class_name
                for class_name in venue_badge.classes
                if class_name.startswith("badge--")
            }
            expected_venue_classes = {"badge--venue", expected_tier_class}
            if (
                "badge" not in venue_badge.classes
                or tier_modifier_classes != expected_venue_classes
            ):
                problems.append(
                    f"paper {paper['id']}: expected only venue tier class "
                    f"'{expected_tier_class}', got {sorted(tier_modifier_classes)}"
                )
            expected_tier_label = VENUE_TIER_LABELS[expected_tier]
            if venue_badge.title != expected_tier_label:
                problems.append(
                    f"paper {paper['id']}: expected venue title "
                    f"'{expected_tier_label}', got '{venue_badge.title}'"
                )

    # Every post page and published course page must exist.
    for post in data.posts:
        if not (DIST_DIR / "blogs" / f"{post['slug']}.html").exists():
            problems.append(f"blog page missing: blogs/{post['slug']}.html")
    for course in data.teaching["courses"]:
        if course.get("published") and not (
            DIST_DIR / "teaching" / f"{course['slug']}.html"
        ).exists():
            problems.append(f"course page missing: teaching/{course['slug']}.html")

    documents = {page.resolve(): Document(page.read_text(encoding="utf-8")) for page in DIST_DIR.rglob("*.html")}
    site_url = data.profile["site"]["base_url"]
    problems.extend(check_links(DIST_DIR, documents, site_url))
    for page in page_registry(data):
        document = documents.get(local_target(DIST_DIR, page.path))
        if document is None:
            problems.append(f"page missing: {page.path}")
            continue
        if document.h1_count != 1:
            problems.append(f"{page.path}: expected one h1, found {document.h1_count}")
        if document.title.strip() != page.title:
            problems.append(f"{page.path}: missing or incorrect page title")
        expected_url = f"{site_url}/{page.path}"
        if document.canonicals != [expected_url]:
            problems.append(f"{page.path}: expected one canonical URL {expected_url}")
        for key, value in (("description", page.description), ("og:title", page.title), ("og:description", page.description), ("og:url", expected_url)):
            if document.meta.get(key) != value:
                problems.append(f"{page.path}: missing or incorrect {key} metadata")
        if not page.indexed and document.meta.get("robots") != "noindex":
            problems.append(f"{page.path}: non-indexed page missing noindex metadata")
    sitemap_path = DIST_DIR / "sitemap.xml"
    if not sitemap_path.is_file():
        problems.append("sitemap.xml missing")
    else:
        actual = [node.text for node in ElementTree.parse(sitemap_path).findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
        expected = [f"{site_url}/{page.path}" for page in page_registry(data) if page.indexed]
        if actual != expected:
            problems.append("sitemap.xml does not match indexed page registry")
    robots = DIST_DIR / "robots.txt"
    if not robots.is_file() or f"Sitemap: {site_url}/sitemap.xml" not in robots.read_text(encoding="utf-8"):
        problems.append("robots.txt missing sitemap declaration")

    _fail(problems)
    print(f"Site checks passed ({len(data.papers)} papers, {len(data.posts)} posts).")
