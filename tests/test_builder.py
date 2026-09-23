"""Behavior regressions for authoring safety, URLs, math, and deployment output."""

from contextlib import redirect_stdout
import copy
from io import StringIO
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import build
from builder import checks, config, data, markdown, site
from builder.render import link_attrs, md_links, site_env
from builder.validation import DataError, local_target, slug_value, url_value


class DataValidationTests(unittest.TestCase):
    def setUp(self):
        self.content = data.load_all()

    def test_slug_rejects_path_and_url_characters(self):
        for value in ("", "../index", "../../outside", "/absolute", "a/b", r"a\b", "a#b", "%2e%2e", " a", 3):
            with self.subTest(value=value), self.assertRaises(DataError):
                slug_value(value, "slug")
        self.assertEqual(slug_value("2026-02-07-real_analysis", "slug"), "2026-02-07-real_analysis")

    def test_courses_and_posts_enforce_slug_policy(self):
        self.content.teaching["courses"][0]["slug"] = "../../outside"
        with self.assertRaises(DataError):
            data._validate_teaching(self.content.teaching)
        with patch.object(Path, "read_text", return_value="---\nslug: ../../outside\n---\nBody"):
            with self.assertRaises(DataError):
                markdown.load_post(Path("2026-01-01-demo.md"))

    def test_output_resolution_rejects_traversal(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "dist"
            root.mkdir()
            for path in ("../outside", "%2e%2e/outside", r"..\outside"):
                with self.subTest(path=path), self.assertRaises(DataError):
                    local_target(root, path)
            self.assertEqual(local_target(root, "/index.html"), root.resolve() / "index.html")

    def test_output_resolution_rejects_symlink_escape(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "dist"
            root.mkdir()
            try:
                (root / "external").symlink_to(Path(folder), target_is_directory=True)
            except OSError as exc:
                if os.name == "nt" and getattr(exc, "winerror", None) == 1314:
                    self.skipTest("Windows symlink creation requires Developer Mode or administrator privileges")
                raise
            with self.assertRaises(DataError):
                local_target(root, "external/private")

    def test_urls_reject_executable_or_ambiguous_schemes(self):
        for url in ("javascript:alert(1)#anchor", "data:text/html,test", "vbscript:test", "//example.com", " https://example.com", "https://user:password@example.com", "https://example.com:invalid", "java\nscript:alert(1)"):
            with self.subTest(url=url), self.assertRaises(DataError):
                url_value(url, "test")
        for url in ("https://example.com/a?q=x#y", "mailto:person@example.com", "/assets/notes.pdf", "../index.html#about", "#main"):
            url_value(url, "test")

    def test_required_profile_metadata_and_avatar(self):
        for section, key in (("site", "title"), ("site", "meta_description"), ("site", "base_url"), (None, "avatar")):
            profile = copy.deepcopy(self.content.profile)
            del (profile[section] if section else profile)[key]
            with self.subTest(key=key), self.assertRaises(DataError):
                data._validate_profile(profile)

    def test_profile_base_url_is_canonical_https_origin(self):
        for value in ("http://example.com", "https://example.com/subpath", "https://example.com?q=x", "https://example.com#x"):
            profile = copy.deepcopy(self.content.profile)
            profile["site"]["base_url"] = value
            with self.subTest(value=value), self.assertRaises(DataError):
                data._validate_profile(profile)

    def test_wrong_content_types_fail_with_data_error(self):
        for key, value in (("year", True), ("selected", "false"), ("authors", "Wei You"), ("title", {}), ("links", {}), ("volume", 3)):
            paper = copy.deepcopy(self.content.papers[0])
            paper[key] = value
            with self.subTest(key=key), self.assertRaises(DataError):
                data._validate_papers({"papers": [paper]})
        self.content.team["students"][0]["placement"] = {"bad": "object"}
        with self.assertRaises(DataError):
            data._validate_team(self.content.team)

    def test_duplicate_ids_and_authorship_mismatches(self):
        paper = self.content.papers[0]
        with self.assertRaisesRegex(DataError, "duplicate"):
            data._validate_papers({"papers": [paper, copy.deepcopy(paper)]})
        paper["student_authors"] = ["Not an author"]
        with self.assertRaisesRegex(DataError, "not in authors"):
            data._validate_papers({"papers": [paper]})

    def test_analytics_can_be_explicitly_disabled(self):
        with patch.dict(os.environ, {config.GA_MEASUREMENT_ID_ENV: ""}):
            self.assertEqual(config.ga_id("G-ABC123"), "")
        with patch.dict(os.environ, {config.GA_MEASUREMENT_ID_ENV: "not-an-id"}):
            with self.assertRaises(DataError):
                config.ga_id("G-ABC123")

    def test_inline_profile_links_escape_and_validate(self):
        self.assertIn("&lt;script&gt;", md_links("<script>"))
        self.assertIn('rel="noopener noreferrer"', md_links("[Example](https://example.com)"))
        with self.assertRaises(DataError):
            md_links("[bad](javascript:alert%281%29#anchor)")

    def test_link_attributes_follow_url_scheme_and_pdf_path(self):
        for url in ("http://example.com", "HTTPS://example.com", "assets/notes.PDF?download=1#page=2", "../notes.pdf"):
            with self.subTest(url=url):
                self.assertEqual(str(link_attrs(url)), ' target="_blank" rel="noopener noreferrer"')
        for url in ("#paper.pdf", "?q=paper.pdf", "mailto:reader@example.pdf", "index.html", "notes.pdf.html"):
            with self.subTest(url=url):
                self.assertEqual(str(link_attrs(url)), "")
        for url in ("javascript:alert(1)", "//example.com/file.pdf", " https://example.com", r"assets\notes.pdf"):
            with self.subTest(url=url), self.assertRaises(DataError):
                link_attrs(url)

    def test_shared_link_attributes_preserve_html_escaping(self):
        url = 'https://example.com/?q="&x=1'
        template = site_env().from_string('<a href="{{ url }}"{{ link_attrs(url) }}>{{ label }}</a>')
        rendered = template.render(url=url, label="<label>")
        self.assertIn('href="https://example.com/?q=&#34;&amp;x=1"', rendered)
        self.assertIn('&lt;label&gt;</a>', rendered)
        self.assertEqual(rendered, md_links(f'[<label>]({url})'))


class MarkdownTests(unittest.TestCase):
    def test_invalid_dates_report_source_filename(self):
        for value in ("2026-99-99", "2026-02-30", "yesterday", ""):
            with self.subTest(value=value), patch.object(Path, "read_text", return_value=f"---\ntitle: Demo\ndate: {value}\nsummary: Demo note\n---\nBody"):
                with self.assertRaisesRegex(DataError, "demo.md: blog date"):
                    markdown.load_post(Path("2026-01-01-demo.md"))
        self.assertEqual(markdown._normalize_date("2024-02-29"), "2024-02-29")

    def test_post_requires_explicit_title_date_and_summary(self):
        metadata = {"title": "Demo", "date": "2026-01-01", "summary": "A demo note."}
        for key in metadata:
            for empty in (False, True):
                fields = dict(metadata)
                if empty:
                    fields[key] = ""
                else:
                    del fields[key]
                raw = "---\n" + "\n".join(f"{name}: {value}" for name, value in fields.items()) + "\n---\nBody"
                with self.subTest(field=key, empty=empty), patch.object(Path, "read_text", return_value=raw):
                    with self.assertRaisesRegex(DataError, f"demo.md: blog {key}"):
                        markdown.load_post(Path("2026-01-01-demo.md"))

    def test_malformed_front_matter_fails_clearly(self):
        for raw in ("Body without metadata", "---\n---\nBody", "---\ntitle: Missing end", "---\ntitle: One\ntitle: Two\n---\nBody", "---\ntitle missing colon\n---\nBody"):
            with self.subTest(raw=raw), self.assertRaises(DataError):
                markdown.parse_front_matter(raw)

    def test_math_is_rendered_without_placeholder_corruption(self):
        body, toc = markdown.to_html("## Math $x^2$ heading\n\nA literal @@MATHSEG0@@ and $x<y$.\n\n$$\na & b > c\n$$")
        self.assertIn('class="arithmatex"', body)
        self.assertIn("x&lt;y", body)
        self.assertIn("a &amp; b &gt; c", body)
        self.assertIn("@@MATHSEG0@@", body)
        self.assertNotIn("MATHSEG", toc[0]["title"])
        self.assertIn("x^2", toc[0]["title"])
        _, comparison_toc = markdown.to_html("## Comparison $a<b, c>d$")
        self.assertIn("a<b, c>d", comparison_toc[0]["title"])

    def test_code_and_mermaid_are_not_parsed_as_page_math(self):
        body, _ = markdown.to_html('`$x$`\n\n```tex\n$x<y$\n```\n\n```mermaid\ngraph LR\nA["$$x$$"] --> B\n```')
        self.assertNotIn('class="arithmatex"', body)
        self.assertIn("<code>$x$</code>", body)
        self.assertIn("$x&lt;y$", body)
        self.assertIn('<code class="language-tex">', body)
        self.assertIn('<pre class="mermaid">', body)
        self.assertIn("$$x$$", body)

    def test_code_markup_is_independent_of_pygments_availability(self):
        source = '```python\nprint("hello")\n```\n\n```tex\n$x<y$\n```'
        with patch("pymdownx.highlight.pygments", False):
            without_pygments = markdown.to_html(source)
        with patch("pymdownx.highlight.pygments", True):
            with_pygments = markdown.to_html(source)
        self.assertEqual(without_pygments, with_pygments)
        self.assertIn('class="language-python"', with_pygments[0])

    def test_task_lists_and_aligned_tables_remain_supported(self):
        body, _ = markdown.to_html('- [x] Done\n- [ ] Open\n\n| A | B |\n| :- | -: |\n| x | y |')
        self.assertIn('type="checkbox"', body)
        self.assertIn("disabled", body)
        self.assertIn('style="text-align: right;"', body)

    def test_authored_html_preserves_layout_but_rejects_execution(self):
        body, _ = markdown.to_html('<figure class="example"><img src="../assets/picture.png" alt="Example"></figure>')
        self.assertIn('<figure class="example">', body)
        for raw in ('<script>alert(1)</script>', '<img src="x.png" onerror="alert(1)">', '[bad](javascript:alert%281%29#x)', '<iframe src="https://example.com"></iframe>'):
            with self.subTest(raw=raw), self.assertRaises(DataError):
                markdown.to_html(raw)
        markdown.to_html('```html\n<script>alert(1)</script>\n```')


class HTMLLinkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "dist"
        self.root.mkdir()
        self.index = self.root / "index.html"
        self.index.write_text('<h1 id="home">Home</h1>')
        (self.root / "sub").mkdir()
        (self.root / "sub" / "index.html").write_text('<h1 id="good">Subpage</h1>')
        (self.root / "notes file.pdf").write_bytes(b"%PDF-test")
        (self.root.parent / "private.txt").write_text("outside artifact")

    def check(self, source):
        documents = {self.index.resolve(): checks.Document(source)}
        return checks.check_links(self.root, documents, "https://example.com")

    def test_links_with_fragments_are_actually_checked(self):
        for url in ("missing.html#section", "sub/#missing", "#missing", "../private.txt", "%2e%2e/private.txt", "javascript:alert(1)#ok"):
            with self.subTest(url=url):
                self.assertTrue(self.check(f'<a href="{url}">link</a>'))

    def test_parser_handles_unquoted_urls_and_root_relative_targets(self):
        self.assertTrue(self.check("<a HREF=missing.html#section>bad</a>"))
        self.assertFalse(self.check('<h1 id="home">Home</h1><a href="/sub/#good">sub</a><a href="notes%20file.pdf?page=1#page=2">PDF</a><a href="https://example.com/sub/index.html#good">canonical</a><a href="#home">home</a>'))

    def test_duplicate_ids_and_inline_handlers_fail(self):
        self.assertTrue(self.check('<div id="same"></div><span id="same"></span>'))
        self.assertTrue(self.check('<button onclick="alert(1)">Click</button>'))

    def test_refresh_destinations_are_checked_like_links(self):
        self.assertTrue(self.check('<meta http-equiv="refresh" content="0;url=missing.html#section">'))
        self.assertTrue(self.check('<meta http-equiv="refresh" content="0;url=javascript:alert(1)#ok">'))


class RegistryTests(unittest.TestCase):
    def test_static_asset_hashes_are_stable_and_follow_content(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            script = root / "site.js"
            script.write_text("first version")
            first = site.static_asset_versions(root)
            os.utime(script, None)
            self.assertEqual(site.static_asset_versions(root), first)
            script.write_text("second version")
            self.assertNotEqual(site.static_asset_versions(root)["site.js"], first["site.js"])

    def test_representative_venue_classification(self):
        cases = [("Operations Research", "OR", "utd24"), ("Production and Operations Management", "POM", "utd24"), ("Journal of Machine Learning Research", "JMLR", "other"), ("Columbia University", "Columbia", "other")]
        for name, abbreviation, tier in cases:
            with self.subTest(name=name):
                self.assertEqual(config.venue_metadata(name).abbreviation, abbreviation)
                self.assertEqual(config.venue_tier(name), tier)
        self.assertEqual(config.venue_tier_from_memberships({"ft50"}), "ft50")
        self.assertEqual(config.venue_tier_from_memberships({"utd24", "ft50"}), "utd24")
        with self.assertRaises(ValueError):
            config.venue_metadata("Unknown Test Venue")

    def test_citation_formatting(self):
        self.assertEqual(config.paper_citation({"type": "working", "status": "Under review"}), "Under review")
        self.assertEqual(config.paper_citation({"type": "journal", "venue": "Operations Research", "volume": "74", "number": "2", "pages": "1-20"}), "Operations Research, 74(2), 1–20")
        self.assertEqual(config.paper_citation({"type": "conference", "venue_display": "Proceedings of Conference", "venue": "Conference"}), "Proceedings of Conference")
        self.assertEqual(config.paper_citation({"type": "journal", "venue": None}), "")

    def test_content_loading_only_requires_editorial_json(self):
        with patch.object(data, "_load_json", wraps=data._load_json) as load_json:
            data.load_all()
        self.assertEqual(
            {call.args[0] for call in load_json.call_args_list},
            {"profile.json", "papers.json", "talks.json", "team.json", "teaching.json"},
        )


class BuiltArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name) / "dist"
        cls.content = data.load_all()
        with patch.object(site, "DIST_DIR", cls.root), redirect_stdout(StringIO()):
            site.build_site(cls.content)

    def test_complete_build_passes_structural_checks(self):
        with patch.object(checks, "DIST_DIR", self.root), redirect_stdout(StringIO()):
            checks.check_site(self.content)

    def test_inline_theme_matches_csp_hash_and_policy_precedes_scripts(self):
        import base64
        import hashlib
        import re
        from html import unescape

        for page in self.root.rglob("*.html"):
            source = page.read_text(encoding="utf-8")
            policy_match = re.search(r'http-equiv="Content-Security-Policy" content="([^"]+)"', source)
            self.assertIsNotNone(policy_match, page.name)
            policy = unescape(policy_match.group(1))
            script_policy = next(part.strip() for part in policy.split(";") if part.strip().startswith("script-src "))
            self.assertNotIn("'unsafe-inline'", script_policy)
            self.assertNotIn("'unsafe-eval'", script_policy)
            scripts = re.findall(r"<script>(.*?)</script>", source, re.DOTALL)
            self.assertEqual(len(scripts), 1)
            self.assertLess(policy_match.start(), source.index("<script"))
            for script in scripts:
                digest = base64.b64encode(hashlib.sha256(script.encode("utf-8")).digest()).decode("ascii")
                self.assertIn(f"'sha256-{digest}'", script_policy)

    def test_home_person_data_preserves_current_profile_and_share_image(self):
        import json
        import re

        source = (self.root / "index.html").read_text(encoding="utf-8")
        person = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', source, re.DOTALL).group(1))
        self.assertEqual(person["@type"], "Person")
        self.assertEqual(person["name"], self.content.profile["name"])
        self.assertEqual(person["image"], site.build_context(self.content)["share_image_url"])
        document = checks.Document(source)
        self.assertEqual(document.meta["og:image"], person["image"])
        self.assertEqual(document.meta["twitter:image"], person["image"])
        for page in self.root.rglob("*.html"):
            if page.name != "index.html":
                self.assertNotIn('type="application/ld+json"', page.read_text(encoding="utf-8"))

    def test_current_downloads_match_their_source_bytes(self):
        for source in config.ASSETS_DIR.rglob("*.pdf"):
            destination = self.root / "assets" / source.relative_to(config.ASSETS_DIR)
            with self.subTest(source=source.name):
                self.assertEqual(destination.read_bytes(), source.read_bytes())
        self.assertEqual((self.root / "CV.pdf").read_bytes(), config.CV_PDF.read_bytes())

    def test_rebuild_removes_obsolete_outputs(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "dist"
            (root / "papers").mkdir(parents=True)
            (root / "papers" / "old.pdf").write_bytes(b"obsolete")
            (root / "talks.html").write_text("obsolete redirect")
            with patch.object(site, "DIST_DIR", root), redirect_stdout(StringIO()):
                site.build_site(self.content)
            self.assertFalse((root / "papers").exists())
            self.assertFalse((root / "talks.html").exists())
            self.assertEqual(
                {path.relative_to(root).as_posix() for path in root.rglob("*.html")},
                {page.path for page in site.page_registry(self.content)},
            )

    def test_sitemap_lists_current_pages_and_excludes_404(self):
        sitemap = (self.root / "sitemap.xml").read_text()
        self.assertNotIn("404.html", sitemap)
        self.assertIn("/blogs/2026-02-07-real_analysis.html", sitemap)
        self.assertTrue((self.root / "404.html").is_file())


class PreviewTests(unittest.TestCase):
    def test_preview_binds_loopback_by_default(self):
        import http.server
        with patch("sys.argv", ["build.py", "--serve"]), patch.object(build.data, "load_all"), patch.object(build.site, "build_site"), patch.object(build.checks, "check_site"), patch.object(http.server, "ThreadingHTTPServer") as server, redirect_stdout(StringIO()):
            self.assertEqual(build.main(), 0)
        self.assertEqual(server.call_args.args[0], ("127.0.0.1", 8000))


if __name__ == "__main__":
    unittest.main()
