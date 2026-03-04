from __future__ import annotations

import json

from .common import (
    BADGE_LABELS,
    RESEARCH_DATA_PATH,
    escape_html,
)

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


def render_research_sections() -> dict[str, object]:
    papers, highlighted = load_research_data()
    return {
        "paper_count": len(papers),
        "selected_markup": build_selected_papers_markup(papers),
        "research_markup": build_research_markup(papers, highlighted),
    }


def build_research() -> int:
    payload = render_research_sections()
    paper_count = int(payload["paper_count"])
    print(f"Built research section from {paper_count} entries.")
    return paper_count
