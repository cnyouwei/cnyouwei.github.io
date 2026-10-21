"""Verify paper-card badges, citations, search text, and matching CSS in CI."""

from contextlib import redirect_stdout
from dataclasses import dataclass, field
from html.parser import HTMLParser
from io import StringIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from markupsafe import escape as jinja_escape

from builder import data, site
from builder.config import (
    BADGE_LABELS,
    VENUE_TIER_LABELS,
    paper_citation,
    venue_metadata,
    venue_tier,
)


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


def paper_card_problems(dist: Path, papers: list[dict]) -> list[str]:
    problems: list[str] = []

    index = dist / "index.html"
    if not index.exists():
        return ["dist/index.html was not generated"]
    index_html = index.read_text(encoding="utf-8")
    parser = _PaperCardParser()
    parser.feed(index_html)
    parser.close()
    paper_cards = parser.cards
    expected_paper_ids = {paper["id"] for paper in papers}

    site_css = dist / "css" / "site.css"
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
    for paper in papers:
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

    return problems


class PaperCardTests(unittest.TestCase):
    def test_publication_status_is_visible_in_citation(self):
        for paper_type in ("journal", "conference"):
            with self.subTest(paper_type=paper_type):
                self.assertEqual(
                    paper_citation({
                        "type": paper_type,
                        "venue": "Naval Research Logistics",
                        "status": "Forthcoming",
                    }),
                    "Naval Research Logistics, Forthcoming",
                )

    def test_conditional_accept_working_status_is_unchanged(self):
        status = "Conditional Accept at Production and Operations Management"
        self.assertEqual(
            paper_citation({
                "type": "working",
                "venue": "Production and Operations Management",
                "status": status,
            }),
            status,
        )

    def test_published_citation_without_status_is_unchanged(self):
        self.assertEqual(
            paper_citation({
                "type": "journal",
                "venue": "Operations Research",
                "volume": "74",
                "number": "2",
                "pages": "879-897",
            }),
            "Operations Research, 74(2), 879–897",
        )

    def test_cards_match_paper_data(self):
        content = data.load_all()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "dist"
            with patch.object(site, "DIST_DIR", root), redirect_stdout(StringIO()):
                site.build_site(content)
            self.assertEqual(paper_card_problems(root, content.papers), [])


if __name__ == "__main__":
    unittest.main()
