"""Post-build sanity checks: did every piece of data make it into the output?

Cheap, dependency-free verification run at the end of every build, so a broken
template or a renamed asset fails the build instead of shipping.
"""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree

from markupsafe import escape as jinja_escape

from .config import DIST_DIR, PUBLISHED_UNLINKED_PDFS
from .data import SiteData
from .site import page_registry
from .validation import DataError, local_target, url_value


class Document(HTMLParser):
    """Collect actual HTML attributes instead of interpreting HTML with regexes."""

    def __init__(self, source: str) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.paper_ids: set[str] = set()
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
            if tag == "article" and element_id.startswith("paper-"):
                self.paper_ids.add(element_id)
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
            if key in {"og:image", "twitter:image"} and attributes.get("content"):
                self.urls.append(attributes["content"])
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


def check_links(
    root: Path, documents: dict[Path, Document], site_url: str = "", found: set[Path] | None = None
) -> list[str]:
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
                if found is not None:
                    found.add(target)
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


def check_pdf_inventory(assets: Path, linked: set[Path]) -> list[str]:
    """Public PDFs have a page link or an explicit legacy-URL exception.

    Other assets may be loaded by CSS or scripts; page links alone cannot
    establish that an image, font, or runtime dependency is unused.
    """
    problems = []
    published = {
        path.relative_to(assets).as_posix(): path.resolve()
        for path in assets.rglob("*")
        if path.is_file() and path.suffix.lower() == ".pdf"
    }
    for name, path in sorted(published.items()):
        if path not in linked and name not in PUBLISHED_UNLINKED_PDFS:
            problems.append(
                f"assets/{name}: PDF is not linked from any page; link it or "
                "list an intentional legacy URL in PUBLISHED_UNLINKED_PDFS"
            )
    for name in sorted(PUBLISHED_UNLINKED_PDFS):
        if name not in published:
            problems.append(f"PUBLISHED_UNLINKED_PDFS: assets/{name} is not a published PDF")
        elif published[name] in linked:
            problems.append(f"PUBLISHED_UNLINKED_PDFS: assets/{name} is linked; remove it from the list")
    return problems


class CheckError(Exception):
    pass


def _fail(problems: list[str]) -> None:
    if problems:
        bullet_list = "\n".join(f"  - {p}" for p in problems)
        raise CheckError(f"Build verification failed:\n{bullet_list}")


def check_site(data: SiteData) -> None:
    problems: list[str] = []

    documents = {page.resolve(): Document(page.read_text(encoding="utf-8")) for page in DIST_DIR.rglob("*.html")}
    site_url = data.profile["site"]["base_url"]
    linked: set[Path] = set()
    problems.extend(check_links(DIST_DIR, documents, site_url, linked))
    problems.extend(check_pdf_inventory(DIST_DIR / "assets", linked))

    # Every paper reaches the homepage (duplicate ids are caught above).
    # Card markup is verified by tests/test_paper_cards.py.
    home = documents.get(local_target(DIST_DIR, "index.html"))
    if home is not None:
        index_html = (DIST_DIR / "index.html").read_text(encoding="utf-8")
        expected_ids = {f"paper-{paper['id']}" for paper in data.papers}
        for unexpected in sorted(home.paper_ids - expected_ids):
            problems.append(f"unexpected paper card on home page: {unexpected[6:]}")
        for paper in data.papers:
            if (
                f"paper-{paper['id']}" not in home.paper_ids
                or str(jinja_escape(paper["title"])) not in index_html
            ):
                problems.append(f"paper missing from home page: {paper['id']}")

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
