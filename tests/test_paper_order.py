"""Working papers follow recorded public update dates, not publication years."""
import copy
import unittest
from builder import data, site
from builder.validation import DataError

class PaperOrderTests(unittest.TestCase):
    def test_latest_update_first(self):
        content = data.load_all()
        ctx = site.build_context(content)
        self.assertEqual([p["id"] for p in ctx["working_papers"]], [
            "interchange-join-shortest-queue", "interchange-join-shortest-queue-rv",
            "cost-aware-structured-bandits", "frank-wolfe-self-play", "principal-fairness-ot"])
        self.assertNotIn("note", next(p for p in content.papers if p["id"] == "interchange-join-shortest-queue"))

    def test_updated_rejects_invalid_date(self):
        content = data.load_all()
        content.papers[0]["updated"] = "2026-02-30"
        with self.assertRaises(DataError):
            data._validate_papers({"papers": content.papers, "highlight_authors": content.highlight_authors})
