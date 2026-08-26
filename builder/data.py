"""Load and validate everything under data/.

The goal is to fail loudly at build time with a precise message, so a typo in
a JSON file never ships as a silently broken page or CV entry.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import markdown as md
from .config import (
    BLOG_SOURCE_DIR,
    DATA_DIR,
    PAPER_TYPES,
    ROOT,
    venue_metadata,
)


class DataError(Exception):
    """A problem in a data/ file that must be fixed before building."""


@dataclass
class SiteData:
    profile: dict[str, Any]
    papers: list[dict[str, Any]]
    highlight_authors: list[str]
    talks: dict[str, Any]
    team: dict[str, Any]
    teaching: dict[str, Any]
    posts: list[dict[str, Any]] = field(default_factory=list)


def _load_json(name: str) -> dict[str, Any]:
    path = DATA_DIR / name
    if not path.exists():
        raise DataError(f"Missing data file: {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DataError(f"{path}: invalid JSON — {exc}") from exc
    if not isinstance(raw, dict):
        raise DataError(f"{path}: top level must be a JSON object")
    # Keys starting with "_" are documentation, not data.
    return {k: v for k, v in raw.items() if not k.startswith("_")}


def _require(obj: dict[str, Any], key: str, where: str) -> Any:
    if key not in obj or obj[key] in (None, "", []):
        raise DataError(f"{where}: missing required field '{key}'")
    return obj[key]


def _check_local_url(url: str, where: str) -> None:
    """Local links (assets/..., blogs/..., teaching/...) must exist or be generated."""
    if url.startswith(("http://", "https://", "mailto:", "#")):
        return
    if url.startswith("assets/"):
        if not (ROOT / url).exists():
            raise DataError(f"{where}: linked file does not exist: {url}")
    # blogs/... and teaching/... are validated post-build by builder.checks.


def _validate_papers(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    papers = _require(payload, "papers", "papers.json")
    highlight = payload.get("highlight_authors", [])
    seen_ids: set[str] = set()
    for paper in papers:
        pid = _require(paper, "id", "papers.json entry")
        where = f"papers.json[{pid}]"
        if pid in seen_ids:
            raise DataError(f"{where}: duplicate id")
        seen_ids.add(pid)

        _require(paper, "title", where)
        ptype = _require(paper, "type", where)
        if ptype not in PAPER_TYPES:
            raise DataError(f"{where}: type '{ptype}' not in {PAPER_TYPES}")
        year = _require(paper, "year", where)
        if not isinstance(year, int):
            raise DataError(f"{where}: year must be an integer")
        authors = _require(paper, "authors", where)
        if not isinstance(authors, list) or not all(isinstance(a, str) for a in authors):
            raise DataError(f"{where}: authors must be a list of names")

        if "venue_abbrev" in paper:
            raise DataError(
                f"{where}: remove 'venue_abbrev'; it is inferred from 'venue'"
            )
        venue = paper.get("venue")
        if venue is not None:
            if not isinstance(venue, str) or not venue.strip():
                raise DataError(f"{where}: venue must be a non-empty string or null")
            try:
                venue_metadata(venue)
            except ValueError as exc:
                raise DataError(f"{where}: {exc}") from exc

        venue_display = paper.get("venue_display")
        if venue_display is not None and (
            not isinstance(venue_display, str) or not venue_display.strip()
        ):
            raise DataError(f"{where}: venue_display must be a non-empty string")
        if venue_display is not None:
            if venue is None:
                raise DataError(f"{where}: venue_display requires a canonical venue")
            if venue.casefold() not in venue_display.casefold():
                raise DataError(
                    f"{where}: venue_display must contain the canonical venue '{venue}'"
                )
        if ptype == "working":
            status = _require(paper, "status", where)
            if not isinstance(status, str) or not status.strip():
                raise DataError(f"{where}: status must be a non-empty string")
            if venue is not None and not status.casefold().endswith(venue.casefold()):
                raise DataError(
                    f"{where}: working-paper status must end with its canonical "
                    f"venue '{venue}'"
                )

        for extra in ("student_authors", "corresponding"):
            for name in paper.get(extra, []):
                if name not in authors:
                    raise DataError(f"{where}: {extra} name '{name}' not in authors")

        for link in paper.get("links", []):
            _require(link, "label", f"{where} link")
            url = _require(link, "url", f"{where} link")
            _check_local_url(url, where)
    return papers, highlight


def _validate_profile(profile: dict[str, Any]) -> dict[str, Any]:
    for key in ("name", "email", "position", "links", "education", "site"):
        _require(profile, key, "profile.json")
    _require(profile["site"], "ga_id", "profile.json site")
    avatar = profile.get("avatar", {})
    if avatar:
        _check_local_url(avatar.get("src", ""), "profile.json avatar")
    for entry in profile["education"]:
        _require(entry, "degree", "profile.json education")
        _require(entry, "institution", "profile.json education")
        thesis = entry.get("thesis")
        if thesis:
            _check_local_url(thesis.get("url", ""), "profile.json education thesis")
    return profile


def _validate_teaching(payload: dict[str, Any]) -> dict[str, Any]:
    courses = _require(payload, "courses", "teaching.json")
    seen: set[str] = set()
    for course in courses:
        slug = _require(course, "slug", "teaching.json course")
        where = f"teaching.json[{slug}]"
        if slug in seen:
            raise DataError(f"{where}: duplicate slug")
        seen.add(slug)
        for key in ("code", "title", "period", "institution", "summary"):
            _require(course, key, where)
        if not isinstance(course.get("published"), bool):
            raise DataError(f"{where}: 'published' must be true or false")
        if course["published"]:
            for key in ("overview", "modules"):
                _require(course, key, where)
            for module in course["modules"]:
                _require(module, "title", f"{where} module")
                if module.get("link_url"):
                    _check_local_url(module["link_url"], f"{where} module")
    return payload


def _validate_talks(payload: dict[str, Any]) -> dict[str, Any]:
    for talk in _require(payload, "conference_talks", "talks.json"):
        _require(talk, "title", "talks.json conference_talks")
        venues = _require(talk, "venues", f"talks.json[{talk.get('title', '?')}]")
        for venue in venues:
            _require(venue, "venue", f"talks.json[{talk['title']}]")
    for talk in _require(payload, "invited_talks", "talks.json"):
        _require(talk, "host", "talks.json invited_talks")
        _require(talk, "years", f"talks.json invited[{talk.get('host', '?')}]")
    return payload


def _validate_team(payload: dict[str, Any]) -> dict[str, Any]:
    for student in _require(payload, "students", "team.json"):
        name = _require(student, "name", "team.json student")
        where = f"team.json[{name}]"
        _require(student, "degree", where)
        _require(student, "period", where)
        if _require(student, "status", where) not in ("current", "former"):
            raise DataError(f"{where}: status must be 'current' or 'former'")
    return payload


def load_posts() -> list[dict[str, Any]]:
    """Read data/blog/*.md into rendered post dicts, newest first."""
    if not BLOG_SOURCE_DIR.exists():
        return []
    posts = []
    seen_slugs: set[str] = set()
    for source in sorted(BLOG_SOURCE_DIR.glob("*.md")):
        post = md.load_post(source)
        if post["slug"] in seen_slugs:
            raise DataError(f"{source.name}: duplicate blog slug '{post['slug']}'")
        seen_slugs.add(post["slug"])
        posts.append(post)
    posts.sort(key=lambda p: (p["date"], p["title"]), reverse=True)
    return posts


def load_all() -> SiteData:
    papers, highlight = _validate_papers(_load_json("papers.json"))
    return SiteData(
        profile=_validate_profile(_load_json("profile.json")),
        papers=papers,
        highlight_authors=highlight,
        talks=_validate_talks(_load_json("talks.json")),
        team=_validate_team(_load_json("team.json")),
        teaching=_validate_teaching(_load_json("teaching.json")),
        posts=load_posts(),
    )
