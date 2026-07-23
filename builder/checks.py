"""Post-build sanity checks: did every piece of data make it into the output?

Cheap, dependency-free verification run at the end of every build, so a broken
template or a renamed asset fails the build instead of shipping.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import html
from html.parser import HTMLParser
import re

from markupsafe import escape as jinja_escape

from .config import (
    BADGE_LABELS,
    DIST_DIR,
    VENUE_TIER_LABELS,
    venue_metadata,
    venue_tier,
    venue_tier_from_memberships,
)
from .data import SiteData

_HREF = re.compile(r"""(?:href|src)=["']([^"'#]+)["']""")


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


def _paper_citation(paper: dict[str, object]) -> str:
    """Independently reconstruct the citation expected in a generated card."""
    if paper["type"] == "working":
        return str(paper.get("status", ""))
    bits = [str(paper.get("venue_display", paper.get("venue", "")))]
    volume = paper.get("volume")
    if volume:
        number = paper.get("number")
        bits.append(f"{volume}({number})" if number else str(volume))
    pages = paper.get("pages")
    if pages:
        bits.append(str(pages).replace("-", "–"))
    return ", ".join(bit for bit in bits if bit)


class CheckError(Exception):
    pass


def _fail(problems: list[str]) -> None:
    if problems:
        bullet_list = "\n".join(f"  - {p}" for p in problems)
        raise CheckError(f"Build verification failed:\n{bullet_list}")


def check_site(data: SiteData) -> None:
    problems: list[str] = []

    tier_cases = [
        (frozenset({"ft50"}), "ft50", "FT50-only classification"),
        (frozenset({"utd24", "ft50"}), "utd24", "UTD24 precedence"),
    ]
    for memberships, expected_tier, description in tier_cases:
        actual_tier = venue_tier_from_memberships(memberships)
        if actual_tier != expected_tier:
            problems.append(
                f"{description} is broken: expected '{expected_tier}', got '{actual_tier}'"
            )

    venue_cases = [
        ("Columbia University", "Columbia", "other"),
        ("Conference on Learning Theory", "COLT", "other"),
        ("INFORMS Journal on Optimization", "IJOO", "other"),
        ("Journal of Machine Learning Research", "JMLR", "other"),
        ("Journal of the American Statistical Association", "JASA", "other"),
        ("Naval Research Logistics", "NRL", "other"),
        ("Operations Research", "OR", "utd24"),
        ("Operations Research Letters", "ORL", "other"),
        ("Production and Operations Management", "POM", "utd24"),
        ("Queueing Systems", "QUESTA", "other"),
        ("Stochastic Systems", "STSY", "other"),
        ("Winter Simulation Conference", "WSC", "other"),
    ]
    for full_name, expected_abbreviation, expected_tier in venue_cases:
        metadata = venue_metadata(full_name)
        actual_tier = venue_tier(full_name)
        if metadata.abbreviation != expected_abbreviation or actual_tier != expected_tier:
            problems.append(
                f"venue inference is broken for '{full_name}': expected "
                f"'{expected_abbreviation}'/'{expected_tier}', got "
                f"'{metadata.abbreviation}'/'{actual_tier}'"
            )

    try:
        venue_metadata("Unknown Test Venue")
    except ValueError:
        pass
    else:
        problems.append("unknown venue names must fail inference")

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
            for role in ("bg", "text"):
                token = f"--badge-venue-{tier}-{role}:"
                if css_text.count(token) < 2:
                    problems.append(
                        f"venue tier CSS missing light/dark token definitions: {token}"
                    )

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

        metadata = venue_metadata(paper["venue"])
        search_terms = [paper["venue"], metadata.abbreviation]
        if paper.get("venue_display"):
            search_terms.append(paper["venue_display"])
        for search_term in search_terms:
            if search_term.casefold() not in card.search_text.casefold():
                problems.append(
                    f"paper {paper['id']}: data-search missing venue term "
                    f"'{search_term}'"
                )

        expected_citation = _paper_citation(paper)
        actual_citation = " ".join("".join(card.citation_text).split())
        if card.citation_count != 1:
            problems.append(
                f"paper {paper['id']}: expected one venue citation, "
                f"found {card.citation_count}"
            )
        elif actual_citation != expected_citation:
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
        if len(venue_badges) != 1:
            problems.append(
                f"paper {paper['id']}: expected one venue badge, found {len(venue_badges)}"
            )
        else:
            venue_badge = venue_badges[0]
            expected_venue = metadata.abbreviation
            actual_venue = _badge_text(venue_badge)
            if actual_venue != expected_venue:
                problems.append(
                    f"paper {paper['id']}: expected venue badge '{expected_venue}', "
                    f"got '{actual_venue}'"
                )
            expected_tier = venue_tier(paper["venue"])
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
