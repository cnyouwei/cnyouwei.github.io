"""Protect public download URLs and validate local sharing-image metadata."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from builder import checks


class AssetInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.assets = self.root / "assets"
        self.assets.mkdir()
        self.index = self.root / "index.html"
        self.pdf = self.assets / "paper file.PDF"
        self.pdf.write_bytes(b"%PDF-test")

    def links(self, source, page=None):
        linked = set()
        documents = {(page or self.index): checks.Document(source)}
        problems = checks.check_links(self.root, documents, "https://example.com", linked)
        return problems, linked

    def test_pdf_links_resolve_nested_paths_queries_and_fragments(self):
        page = self.root / "blogs" / "post.html"
        page.parent.mkdir()
        for url in (
            "../assets/paper%20file.PDF?download=1#page=2",
            "/assets/paper%20file.PDF",
            "https://example.com/assets/paper%20file.PDF",
        ):
            with self.subTest(url=url):
                problems, linked = self.links(f'<a href="{url}">Paper</a>', page)
                self.assertEqual(problems, [])
                self.assertEqual(linked, {self.pdf})
                with patch.object(checks, "PUBLISHED_UNLINKED_PDFS", frozenset()):
                    self.assertEqual(checks.check_pdf_inventory(self.assets, linked), [])

    def test_new_unlinked_pdf_requires_an_explicit_legacy_entry(self):
        with patch.object(checks, "PUBLISHED_UNLINKED_PDFS", frozenset()):
            problems = checks.check_pdf_inventory(self.assets, set())
        self.assertEqual(len(problems), 1)
        self.assertIn("assets/paper file.PDF", problems[0])
        with patch.object(checks, "PUBLISHED_UNLINKED_PDFS", frozenset({"paper file.PDF"})):
            self.assertEqual(checks.check_pdf_inventory(self.assets, set()), [])

    def test_legacy_inventory_rejects_missing_or_now_linked_entries(self):
        for entries, linked, expected in (
            ({"missing.pdf", "paper file.PDF"}, set(), "not a published PDF"),
            ({"paper file.PDF"}, {self.pdf}, "is linked; remove it from the list"),
        ):
            with self.subTest(entries=entries, linked=linked):
                with patch.object(checks, "PUBLISHED_UNLINKED_PDFS", frozenset(entries)):
                    problems = checks.check_pdf_inventory(self.assets, linked)
                self.assertEqual(len(problems), 1)
                self.assertIn(expected, problems[0])

    def test_non_pdf_assets_do_not_need_page_links(self):
        # Fonts and images can be referenced indirectly by CSS or scripts.
        for filename in ("background.webp", "font.woff2", "logo.svg"):
            (self.assets / filename).write_bytes(b"asset")
        with patch.object(checks, "PUBLISHED_UNLINKED_PDFS", frozenset()):
            self.assertEqual(checks.check_pdf_inventory(self.assets, {self.pdf}), [])

    def test_local_social_images_are_checked_and_external_images_are_allowed(self):
        image = self.assets / "share.jpg"
        image.write_bytes(b"image")
        for attribute, name in (("property", "og:image"), ("name", "twitter:image")):
            with self.subTest(name=name):
                problems, linked = self.links(
                    f'<meta {attribute}="{name}" content="https://example.com/assets/share.jpg">'
                )
                self.assertEqual(problems, [])
                self.assertEqual(linked, {image})
                problems, _ = self.links(
                    f'<meta {attribute}="{name}" content="assets/missing.jpg">'
                )
                self.assertTrue(problems)
                problems, linked = self.links(
                    f'<meta {attribute}="{name}" content="https://other.example/share.jpg">'
                )
                self.assertEqual(problems, [])
                self.assertEqual(linked, set())


if __name__ == "__main__":
    unittest.main()
