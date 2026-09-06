"""Load and validate everything under data/.

The goal is to fail loudly at build time with a precise message, so a typo in
a JSON file never ships as a silently broken page.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from . import markdown as md
from .validation import DataError, list_value, local_target, object_value, slug_value, text_value, url_value
from .config import (
    BLOG_SOURCE_DIR,
    DATA_DIR,
    PAPER_TYPES,
    ROOT,
    venue_metadata,
)


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
    object_value(obj, where)
    if key not in obj or obj[key] in (None, "", []):
        raise DataError(f"{where}: missing required field '{key}'")
    return obj[key]


def _check_local_url(url: str, where: str) -> None:
    """Local links (assets/..., blogs/..., teaching/...) must exist or be generated."""
    parsed = url_value(url, where)
    if parsed.scheme:
        return
    target = local_target(ROOT, parsed.path)
    if parsed.path.lstrip("/").startswith("assets/") or parsed.path == "CV.pdf":
        if not target.is_file():
            raise DataError(f"{where}: linked file does not exist: {url}")
    # blogs/... and teaching/... are validated post-build by builder.checks.


def _validate_papers(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    papers = list_value(_require(payload, "papers", "papers.json"), "papers.json papers")
    highlight = _strings(payload.get("highlight_authors", []), "papers.json highlight_authors")
    seen_ids: set[str] = set()
    for paper in papers:
        pid = slug_value(_require(paper, "id", "papers.json entry"), "papers.json id")
        where = f"papers.json[{pid}]"
        if pid in seen_ids:
            raise DataError(f"{where}: duplicate id")
        seen_ids.add(pid)

        text_value(_require(paper, "title", where), f"{where} title")
        ptype = _require(paper, "type", where)
        if ptype not in PAPER_TYPES:
            raise DataError(f"{where}: type '{ptype}' not in {PAPER_TYPES}")
        year = _require(paper, "year", where)
        if type(year) is not int or not 1000 <= year <= 9999:
            raise DataError(f"{where}: year must be an integer")
        authors = _require(paper, "authors", where)
        _strings(authors, f"{where} authors")
        for key in ("topic", "volume", "number", "pages", "abstract", "note", "status"):
            if key in paper:
                text_value(paper[key], f"{where} {key}", empty=key in ("abstract", "note"))
        for key in ("selected", "alphabetical"):
            if key in paper and type(paper[key]) is not bool:
                raise DataError(f"{where}: {key} must be true or false")

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
            for name in _strings(paper.get(extra, []), f"{where} {extra}"):
                if name not in authors:
                    raise DataError(f"{where}: {extra} name '{name}' not in authors")

        for link in list_value(paper.get("links", []), f"{where} links"):
            text_value(_require(link, "label", f"{where} link"), f"{where} link label")
            url = _require(link, "url", f"{where} link")
            _check_local_url(url, where)
    return papers, highlight


def _validate_profile(profile: dict[str, Any]) -> dict[str, Any]:
    for key in ("name", "email", "tagline", "research_focus"):
        text_value(_require(profile, key, "profile.json"), f"profile.json {key}")
    for key in ("position", "bio", "research_interest_tags"):
        _strings(_require(profile, key, "profile.json"), f"profile.json {key}")
    site = object_value(_require(profile, "site", "profile.json"), "profile.json site")
    for key in ("title", "meta_description", "footer_affiliation", "base_url"):
        text_value(_require(site, key, "profile.json site"), f"profile.json site.{key}")
    base = url_value(site["base_url"], "profile.json site.base_url")
    if base.scheme != "https" or base.path not in ("", "/") or base.query or base.fragment:
        raise DataError("profile.json site.base_url: expected an HTTPS origin without a path, query, or fragment")
    site["base_url"] = site["base_url"].rstrip("/")
    ga = site.get("ga_id", "")
    if not isinstance(ga, str) or (ga and not re.fullmatch(r"G-[A-Z0-9]+", ga)):
        raise DataError("profile.json site.ga_id: expected an empty string or G- measurement ID")
    site["ga_id"] = ga
    for link in list_value(_require(profile, "links", "profile.json"), "profile.json links"):
        for key in ("label", "icon"):
            text_value(_require(link, key, "profile.json link"), f"profile.json link {key}")
        _check_local_url(_require(link, "url", "profile.json link"), "profile.json link")
        if "icon_only" in link and type(link["icon_only"]) is not bool:
            raise DataError("profile.json link icon_only: expected true or false")
    _optional_strings(profile, ("name_cn",), "profile.json")
    avatar = object_value(_require(profile, "avatar", "profile.json"), "profile.json avatar")
    _check_local_url(_require(avatar, "src", "profile.json avatar"), "profile.json avatar")
    text_value(_require(avatar, "alt", "profile.json avatar"), "profile.json avatar alt")
    for key in ("width", "height"):
        if type(avatar.get(key)) is not int or avatar[key] <= 0:
            raise DataError(f"profile.json avatar {key}: expected a positive integer")
    for entry in list_value(_require(profile, "education", "profile.json"), "profile.json education"):
        for key in ("degree", "institution", "period"):
            text_value(_require(entry, key, "profile.json education"), f"profile.json education {key}")
        _optional_strings(entry, ("location",), "profile.json education")
        if "thesis" in entry:
            thesis = object_value(entry["thesis"], "profile.json education thesis")
            text_value(_require(thesis, "title", "profile.json education thesis"), "profile.json thesis title")
            _check_local_url(thesis.get("url", ""), "profile.json education thesis")
    return profile


def _validate_teaching(payload: dict[str, Any]) -> dict[str, Any]:
    courses = list_value(_require(payload, "courses", "teaching.json"), "teaching.json courses")
    seen: set[str] = set()
    for course in courses:
        slug = slug_value(_require(course, "slug", "teaching.json course"), "teaching.json slug")
        where = f"teaching.json[{slug}]"
        if slug in seen:
            raise DataError(f"{where}: duplicate slug")
        seen.add(slug)
        for key in ("code", "title", "period", "institution", "summary"):
            text_value(_require(course, key, where), f"{where} {key}")
        if not isinstance(course.get("published"), bool):
            raise DataError(f"{where}: 'published' must be true or false")
        if course["published"]:
            text_value(_require(course, "overview", where), f"{where} overview")
            _strings(course.get("outcomes", []), f"{where} outcomes")
            for key in ("audience", "prerequisites"):
                if key in course:
                    text_value(course[key], f"{where} {key}")
            for module in list_value(_require(course, "modules", where), f"{where} modules"):
                for key in ("title", "description"):
                    text_value(_require(module, key, f"{where} module"), f"{where} module {key}")
                _optional_strings(module, ("code", "link_label", "link_url"), f"{where} module")
                if module.get("link_url"):
                    _check_local_url(module["link_url"], f"{where} module")
    return payload


def _validate_talks(payload: dict[str, Any]) -> dict[str, Any]:
    _optional_strings(payload, ("coauthor_note",), "talks.json")
    for talk in list_value(_require(payload, "conference_talks", "talks.json"), "talks.json conference_talks"):
        text_value(_require(talk, "title", "talks.json conference_talks"), "talks.json title")
        venues = list_value(_require(talk, "venues", f"talks.json[{talk.get('title', '?')}]"), "talks.json venues")
        for venue in venues:
            text_value(_require(venue, "venue", f"talks.json[{talk['title']}]"), "talks.json venue")
            if "by_coauthor" in venue and type(venue["by_coauthor"]) is not bool:
                raise DataError("talks.json by_coauthor: expected true or false")
    for talk in list_value(_require(payload, "invited_talks", "talks.json"), "talks.json invited_talks"):
        text_value(_require(talk, "host", "talks.json invited_talks"), "talks.json host")
        years = list_value(_require(talk, "years", f"talks.json invited[{talk.get('host', '?')}]"), "talks.json years")
        if not years or any(type(year) is not int or not 1000 <= year <= 9999 for year in years):
            raise DataError("talks.json years: expected calendar years as integers")
    return payload


def _validate_team(payload: dict[str, Any]) -> dict[str, Any]:
    for student in list_value(_require(payload, "students", "team.json"), "team.json students"):
        name = _require(student, "name", "team.json student")
        where = f"team.json[{name}]"
        for key in ("name", "degree", "period"):
            text_value(_require(student, key, where), f"{where} {key}")
        if _require(student, "status", where) not in ("current", "former"):
            raise DataError(f"{where}: status must be 'current' or 'former'")
        _optional_strings(student, ("placement", "coadvisor", "institution_note", "thesis"), where)
    return payload


def _strings(value, where: str) -> list[str]:
    return [text_value(item, where) for item in list_value(value, where)]


def _optional_strings(obj: dict, keys: tuple[str, ...], where: str) -> None:
    for key in keys:
        if key in obj:
            text_value(obj[key], f"{where} {key}", empty=True)


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
