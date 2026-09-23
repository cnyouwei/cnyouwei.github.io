"""Standard-library checks for browser coverage driven by the built sitemap."""

from pathlib import Path
import tempfile
import unittest
from xml.etree import ElementTree

from browser_smoke import discover_pages


class BrowserDiscoveryTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.dist = Path(folder.name)
        (self.dist / "404.html").touch()

    def sitemap(self, paths):
        root = ElementTree.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
        for path in paths:
            ElementTree.SubElement(ElementTree.SubElement(root, "url"), "loc").text = f"https://example.com/{path}"
        ElementTree.ElementTree(root).write(self.dist / "sitemap.xml", encoding="utf-8")

    def test_discovers_new_nested_pages_and_adds_404(self):
        paths = ("index.html", "blogs/new-post.html", "teaching/new-course.html")
        for path in paths:
            target = self.dist / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.touch()
        self.sitemap(paths)
        self.assertEqual(discover_pages(self.dist), (*paths, "404.html"))

    def test_empty_and_duplicate_sitemaps_fail(self):
        for paths, message in (([], "no pages"), (["index.html", "index.html"], "Duplicate")):
            with self.subTest(paths=paths):
                self.sitemap(paths)
                with self.assertRaisesRegex(RuntimeError, message):
                    discover_pages(self.dist)

    def test_missing_page_including_404_fails(self):
        self.sitemap(["index.html"])
        with self.assertRaisesRegex(RuntimeError, "Missing built page index.html"):
            discover_pages(self.dist)
        (self.dist / "index.html").touch()
        (self.dist / "404.html").unlink()
        with self.assertRaisesRegex(RuntimeError, "Missing built page 404.html"):
            discover_pages(self.dist)

    def test_unsafe_or_non_page_urls_fail(self):
        for path in ("../outside.html", "%2e%2e/outside.html", r"..\outside.html",
                     "/outside.html", "C:/outside.html", "index.html?query=1", "index.html#anchor", "asset.pdf"):
            with self.subTest(path=path):
                self.sitemap([path])
                with self.assertRaisesRegex(RuntimeError, "Invalid sitemap page"):
                    discover_pages(self.dist)

    def test_missing_and_malformed_sitemap_fail(self):
        for source in (None, "<urlset>"):
            with self.subTest(source=source):
                if source is not None:
                    (self.dist / "sitemap.xml").write_text(source, encoding="utf-8")
                with self.assertRaisesRegex(RuntimeError, "Build a valid sitemap"):
                    discover_pages(self.dist)
