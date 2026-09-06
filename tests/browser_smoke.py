"""Browser regressions for the built site; intentionally outside test_*.py.

python tests/browser_smoke.py                     # deterministic behavior fixtures
python tests/browser_smoke.py --live-dependencies # real CDN rendering; fails if unavailable

Both modes are required in CI. Fixture mode does not claim to verify rendered
equations. The live run waits for real MathJax, Mermaid, images and fonts before
testing horizontal overflow. Neither mode changes source content or deploys.
"""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
import unittest
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).with_name("browser_fixtures")
WIDTHS = (320, 375, 760, 761, 880, 881, 1024, 1440)
PAGES = (
    "index.html",
    "404.html",
    "blogs/2026-02-07-real_analysis.html",
    "blogs/2026-02-09-latex_style_guide.html",
    "teaching/ieda2540.html",
    "teaching/ieda5270.html",
    "teaching/real-analysis-2011.html",
)
LIVE = False
PAPER_COUNT = len(json.loads((ROOT / 'data' / 'papers.json').read_text())["papers"])


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


class BrowserSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for name in PAGES:
            if not (ROOT / "dist" / name).is_file():
                raise RuntimeError("Build the site first: python build.py")
        cls.server = ThreadingHTTPServer(
            ("127.0.0.1", 0), partial(QuietHandler, directory=str(ROOT / "dist"))
        )
        cls.server.daemon_threads = True
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.origin = f"http://127.0.0.1:{cls.server.server_port}"
        cls.playwright = sync_playwright().start()
        try:
            cls.browser = cls.playwright.chromium.launch()
        except Exception:
            cls.playwright.stop()
            cls.server.shutdown()
            cls.server.server_close()
            raise

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        self.contexts = []
        self.errors = []
        self.requests = []

    def tearDown(self):
        for context in self.contexts:
            context.close()
        self.assertEqual(self.errors, [], "Uncaught browser errors")

    def page(self, *, width=375, javascript=True, theme="light", fixture=None, **kwargs):
        context = self.browser.new_context(
            viewport={"width": width, "height": 900},
            java_script_enabled=javascript,
            color_scheme=theme,
            **kwargs,
        )
        self.contexts.append(context)
        use_fixture = not LIVE if fixture is None else fixture

        def route(request):
            url = request.request.url
            self.requests.append(url)
            if url.startswith(self.origin):
                request.continue_()
                return
            host = urlsplit(url).hostname or ""
            # Analytics is never contacted by verification; localhost must disable it.
            if "google-analytics" in host or "googletagmanager" in host:
                request.abort()
                return
            if not use_fixture:
                request.continue_()
                return
            headers = {"access-control-allow-origin": "*"}
            filename = None
            if "/mathjax@" in url and url.endswith("tex-chtml.js"):
                filename = "mathjax.js"
            elif "/mermaid@" in url and url.endswith("mermaid.esm.min.mjs"):
                filename = "mermaid.mjs"
            elif url.endswith("highlight.min.js"):
                filename = "highlight.js"
            if filename:
                request.fulfill(
                    status=200, content_type="text/javascript", headers=headers,
                    body=(FIXTURES / filename).read_text(),
                )
            elif "fonts.googleapis.com" in host or url.endswith(".css"):
                request.fulfill(status=200, content_type="text/css", body="", headers=headers)
            elif "/languages/" in url:
                request.fulfill(status=200, content_type="text/javascript", body="", headers=headers)
            else:
                request.abort()

        context.route("**/*", route)
        page = context.new_page()
        page.set_default_timeout(12_000)
        page.on("pageerror", lambda error: self.errors.append(str(error)))
        return page

    def goto(self, page, name, *, settle=True):
        response = page.goto(f"{self.origin}/{name}", wait_until="load", timeout=45_000)
        self.assertEqual(response.status, 200)
        if settle:
            self.settle(page)

    def settle(self, page):
        page.wait_for_function("""() => document.fonts.status === 'loaded' &&
            Array.from(document.images).filter(image => {
                const rect = image.getBoundingClientRect();
                return image.loading !== 'lazy' || (rect.top < innerHeight && rect.bottom > 0);
            }).every(image => image.complete)
        """, timeout=20_000)
        page.evaluate("""async () => {
            await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
        }""")

    def assert_fits(self, page, label):
        metrics = page.evaluate("""() => ({
            viewport: document.documentElement.clientWidth,
            document: document.documentElement.scrollWidth,
            body: document.body.scrollWidth,
            offenders: Array.from(document.querySelectorAll('body *')).filter(el => {
                const r = el.getBoundingClientRect();
                return r.width && r.right + scrollX > innerWidth + 2;
            }).slice(0, 8).map(el => el.tagName + '.' + el.className)
        })""")
        self.assertLessEqual(max(metrics["body"], metrics["document"]), metrics["viewport"] + 2,
                             f"Horizontal page overflow: {label}: {metrics}")

    def ready_content(self, page, name):
        if name == "index.html":
            page.locator(".paper-abstract").evaluate_all("nodes => nodes.forEach(node => node.open = true)")
        if page.locator('.post-body .arithmatex').count() or name == "index.html":
            page.wait_for_function("window.MathJax && typeof MathJax.typesetPromise === 'function'", timeout=45_000)
            # Queue a final pass through the public helper, after the UI's open events,
            # to ensure every expanded abstract has settled before measuring layout.
            page.evaluate("""async () => {
                await MathJax.startup.promise;
                await window.WY.typesetMath(Array.from(document.querySelectorAll('.post-body, .paper-abstract[open] .paper-abstract-body')));
            }""")
            if LIVE:
                self.assertGreater(page.locator("mjx-container").count(), 0, "Real MathJax did not render")
                self.assertEqual(page.locator("mjx-merror, [data-mjx-error]").count(), 0,
                                 "MathJax rendered a parsing error")
        if "real_analysis" in name:
            page.locator('.mermaid[aria-busy="false"] svg').first.wait_for(timeout=45_000)
            if LIVE:
                self.assertGreater(page.locator(".mermaid svg math").count(), 0,
                                   "Diagram equations must use native MathML")
                self.assertEqual(page.locator(".mermaid .katex-html").count(), 0,
                                 "Legacy CSS math rendering should not be generated")
                self.assertFalse(any("katex.min.css" in url for url in self.requests),
                                 "The separate KaTeX stylesheet should not load")
        self.settle(page)

    def test_all_pages_viewports_and_themes(self):
        for name in PAGES:
            page = self.page(width=1440)
            self.goto(page, name)
            self.ready_content(page, name)
            for theme in ("light", "dark"):
                rerenders_diagram = page.locator(".mermaid svg").count() > 0 and page.locator("html").get_attribute("data-theme") != theme
                if rerenders_diagram:
                    page.evaluate("window.__previousMermaidSvg = document.querySelector('.mermaid svg')")
                page.emulate_media(color_scheme=theme)
                page.wait_for_function("theme => document.documentElement.dataset.theme === theme", arg=theme)
                if rerenders_diagram:
                    page.wait_for_function("""() => {
                        const svg = document.querySelector('.mermaid[data-processed][aria-busy="false"] svg');
                        return svg && svg !== window.__previousMermaidSvg;
                    }""", timeout=45_000)
                for width in WIDTHS:
                    with self.subTest(page=name, theme=theme, width=width, real_dependencies=LIVE):
                        page.set_viewport_size({"width": width, "height": 900})
                        self.settle(page)
                        self.assert_fits(page, f"{name} {theme} {width}px")
                        self.assertEqual(page.locator("h1").count(), 1)
                        if name.startswith("blogs/") and width <= 880:
                            self.assertFalse(page.locator(".post-toc").evaluate("el => el.open"))
                            self.assertLess(page.locator("h1").bounding_box()["y"], 650)
            print(f"  checked {name}: all widths and themes", flush=True)
            page.close()

    def test_no_javascript_content_and_navigation(self):
        for name in PAGES:
            with self.subTest(page=name):
                page = self.page(javascript=False, width=320)
                self.goto(page, name, settle=False)
                self.assert_fits(page, f"{name} without JavaScript")
                self.assertTrue(page.locator("h1").is_visible())
                self.assertTrue(page.locator(".site-nav .nav-link").first.is_visible())
                self.assertFalse(page.locator(".menu-toggle").is_visible())
                if name == "index.html":
                    self.assertFalse(page.locator("[data-research-controls]").is_visible())
                    self.assertEqual(page.locator("article.paper:visible").count(), PAPER_COUNT)
                    page.locator(".site-nav .nav-link").filter(has_text="Research").first.click()
                    page.wait_for_url("**#research")
                    # Poll geometry from the driver: page rAF polling is unreliable
                    # when scripts are disabled, while native smooth scrolling works.
                    for _ in range(50):
                        if 0 <= page.locator("#research").bounding_box()["y"] < 900:
                            break
                        page.wait_for_timeout(50)
                    self.assertEqual(page.locator(".site-header").evaluate("el => getComputedStyle(el).position"), "static")
                    self.assertGreaterEqual(page.locator("#research").bounding_box()["y"], 0)
                    self.assertLess(page.locator("#research").bounding_box()["y"], 900)
                page.close()

    def test_keyboard_and_two_hundred_percent_text(self):
        page = self.page(width=375)
        self.goto(page, "index.html")
        page.keyboard.press("Tab")
        self.assertEqual(page.locator(":focus").get_attribute("class"), "skip-link")
        page.keyboard.press("Enter")
        self.assertEqual(page.locator(":focus").get_attribute("id"), "main")
        menu = page.locator(".menu-toggle")
        menu.focus()
        page.keyboard.press("Enter")
        self.assertEqual(menu.get_attribute("aria-expanded"), "true")
        page.locator(".site-nav .nav-link").first.focus()
        page.keyboard.press("Escape")
        self.assertEqual(menu.get_attribute("aria-expanded"), "false")
        self.assertTrue(menu.evaluate("el => el === document.activeElement"))
        toggle = page.locator(".theme-toggle")
        toggle.focus()
        page.keyboard.press("Space")
        self.assertEqual(page.locator("html").get_attribute("data-theme"), "dark")
        page.reload()
        self.assertEqual(page.locator("html").get_attribute("data-theme"), "dark")
        for name in PAGES:
            self.goto(page, name)
            self.ready_content(page, name)
            # Root text-size emulation doubles rem-based text without shrinking the viewport.
            before = page.locator("body").evaluate("el => parseFloat(getComputedStyle(el).fontSize)")
            page.add_style_tag(content="html { font-size: 200% !important; }")
            self.assertGreaterEqual(page.locator("body").evaluate("el => parseFloat(getComputedStyle(el).fontSize)"), before * 2)
            for width in (375, 761):
                page.set_viewport_size({"width": width, "height": 900})
                self.settle(page)
                self.assert_fits(page, f"{name} 200% text at {width}px")
            page.set_viewport_size({"width": 375, "height": 900})

    def test_filter_empty_recovery_and_grouping(self):
        page = self.page(width=375)
        self.goto(page, "index.html")
        papers = page.locator("article.paper:visible")
        total = papers.count()
        original_ids = papers.evaluate_all("nodes => nodes.map(node => node.id)")
        self.assertEqual(total, PAPER_COUNT)
        page.locator("#paperSearch").fill("no-paper-will-match-this-query")
        page.wait_for_function("document.querySelectorAll('article.paper:not([hidden])').length === 0")
        self.assertIn("0", page.locator("#papers-status").inner_text())
        page.locator("#paperSearch").fill("")
        page.wait_for_function("total => document.querySelectorAll('article.paper:not([hidden])').length === total", arg=PAPER_COUNT)
        page.locator("#typeFilter").select_option("journal")
        self.assertGreater(papers.count(), 0)
        self.assertTrue(all(p == "journal" for p in papers.evaluate_all("nodes => nodes.map(n => n.dataset.type)")))
        page.locator("#typeFilter").select_option("all")
        options = page.locator("#sortOrder option").evaluate_all("nodes => nodes.map(n => n.value)")
        for option in options:
            page.locator("#sortOrder").select_option(option)
            self.assertEqual(papers.count(), total)
            self.assert_fits(page, f"research sort {option}")
        target = page.locator("article.paper[data-type='journal']").first
        target_id = target.get_attribute("id")
        target_topic = target.get_attribute("data-topic")
        target_title = target.locator(".paper-title").inner_text()
        page.locator("#sortOrder").select_option("topic")
        page.locator("#typeFilter").select_option("journal")
        page.locator("#topicFilter").select_option(target_topic)
        page.locator("#paperSearch").fill(target_title)
        self.assertEqual(papers.evaluate_all("nodes => nodes.map(node => node.id)"), [target_id])
        page.locator("#paperSearch").fill("no-paper-will-match-this-query")
        self.assertEqual(papers.count(), 0)
        page.locator("#paperSearch").fill("")
        page.locator("#topicFilter").select_option("all")
        page.locator("#typeFilter").select_option("all")
        page.locator("#sortOrder").select_option(options[0])
        self.assertEqual(papers.evaluate_all("nodes => nodes.map(node => node.id)"), original_ids)

    def test_two_hundred_percent_css_zoom(self):
        # CSS zoom emulates enlargement; it does not drive browser-UI zoom or
        # change matchMedia's viewport. The independent width matrix covers reflow.
        page = self.page(width=1440)
        for name in PAGES:
            self.goto(page, name)
            self.ready_content(page, name)
            page.add_style_tag(content="html { zoom: 2 !important; }")
            self.assertEqual(page.locator("html").evaluate("el => getComputedStyle(el).zoom"), "2")
            self.settle(page)
            self.assert_fits(page, f"{name} 200% CSS zoom at 1440px")

    def test_print_and_reduced_motion(self):
        page = self.page(theme="dark", reduced_motion="reduce")
        snapshot = """() => ({
            controls: Array.from(document.querySelectorAll('[data-research-controls] select, [data-research-controls] input')).map(el => [el.id, el.value]),
            papers: Array.from(document.querySelectorAll('article.paper')).map(el => ({id:el.id, hidden:el.hidden, open:el.querySelector('details')?.open ?? null}))
        })"""
        for name in PAGES:
            self.goto(page, name)
            self.assertEqual(page.locator("html").evaluate("el => getComputedStyle(el).scrollBehavior"), "auto")
            self.assertEqual(page.locator(".reveal").count(), 0)
            saved = None
            if name == "index.html":
                page.locator("#typeFilter").select_option("working")
                page.locator("#sortOrder").select_option("topic")
                page.locator("#paperSearch").fill("queue")
                page.locator("article.paper:visible .paper-abstract").first.evaluate("el => el.open = true")
                saved = page.evaluate(snapshot)
                self.assertLess(page.locator("article.paper:visible").count(), PAPER_COUNT)
            page.emulate_media(media="print")
            self.assertFalse(page.locator(".site-header").is_visible())
            background = page.locator("body").evaluate("el => getComputedStyle(el).backgroundColor")
            self.assertIn(background, ("rgb(255, 255, 255)", "rgba(0, 0, 0, 0)"))
            self.assertTrue(page.locator("h1").is_visible())
            if saved:
                page.wait_for_function("total => document.querySelectorAll('article.paper:not([hidden])').length === total", arg=PAPER_COUNT)
                self.assertEqual(page.locator("article.paper:visible").count(), PAPER_COUNT)
                self.assertEqual(page.locator(".topic-groups").count(), 0)
                self.assertEqual(page.locator(".paper-abstract[open]").count(), page.locator(".paper-abstract").count())
                self.assertEqual(page.locator(".paper-abstract-body:visible").count(), page.locator(".paper-abstract-body").count())
            page.emulate_media(media="screen")
            if saved:
                page.wait_for_function("document.getElementById('typeFilter').value === 'working'")
                self.assertEqual(page.evaluate(snapshot), saved)

    def test_dependency_failure_retry_and_queue(self):
        page = self.page(fixture=True)
        attempts = []

        def fail_first(route):
            attempts.append(route.request.url)
            if len(attempts) == 1:
                route.abort()
            else:
                route.fulfill(status=200, content_type="text/javascript", headers={"access-control-allow-origin": "*"},
                              body=(FIXTURES / "mathjax.js").read_text())

        page.route("**/mathjax@*/**/tex-chtml.js", fail_first)
        self.goto(page, "index.html")
        abstracts = page.locator(".paper-abstract")
        first_math = page.locator("#paper-interchange-join-shortest-queue-rv .paper-abstract")
        first_math.locator("summary").click()
        retry = page.get_by_role("button", name="Retry equations").first
        retry.wait_for()
        self.assertTrue(first_math.locator(".paper-abstract-body").is_visible())
        retry.click()
        page.wait_for_function("window.__mathCalls && __mathCalls.length > 0 && __mathActive === 0")
        self.assertEqual(len(attempts), 2)
        abstracts.nth(1).evaluate("el => el.open = true")
        abstracts.nth(2).evaluate("el => el.open = true")
        page.evaluate("""async () => await Promise.all([
            WY.typesetMath([document.querySelectorAll('.paper-abstract-body')[1]]),
            WY.typesetMath([document.querySelectorAll('.paper-abstract-body')[2]])
        ])""")
        self.assertFalse(page.evaluate("window.__mathOverlap"), "MathJax calls overlapped")
        self.assertEqual(len(attempts), 2, "An already loaded engine was downloaded again")

    def test_delayed_math_and_localhost_analytics(self):
        page = self.page(fixture=True)
        page.route("**/mathjax@*/**/tex-chtml.js", lambda route: route.fulfill(
            status=200, content_type="text/javascript", headers={"access-control-allow-origin": "*"},
            body=(FIXTURES / "mathjax.js").read_text().replace(
                "promise: Promise.resolve()", "promise: new Promise(resolve => setTimeout(resolve, 250))"
            ),
        ))
        self.goto(page, "index.html")
        self.assertTrue(page.locator("h1").is_visible())
        # Source content remains readable while an optional engine is unavailable.
        first_math = page.locator("#paper-interchange-join-shortest-queue-rv .paper-abstract")
        first_math.evaluate("el => el.open = true")
        self.assertTrue(first_math.locator(".paper-abstract-body").is_visible())
        page.wait_for_function("window.__mathCalls && __mathCalls.length > 0 && __mathActive === 0")
        self.assertFalse(any("googletagmanager" in url or "google-analytics" in url for url in self.requests))

    def test_stalled_math_startup_times_out_and_retries(self):
        page = self.page(fixture=True)
        page.add_init_script("""const originalTimeout = window.setTimeout;
            window.setTimeout = (callback, delay, ...args) =>
                originalTimeout(callback, delay === 15000 ? 1000 : delay, ...args);
        """)
        attempts = []

        def stalled_first(route):
            attempts.append(route.request.url)
            source = (FIXTURES / "mathjax.js").read_text()
            if len(attempts) == 1:
                source = source.replace("promise: Promise.resolve()", "promise: new Promise(() => {})")
            route.fulfill(status=200, content_type="text/javascript",
                          headers={"access-control-allow-origin": "*"}, body=source)

        page.route("**/mathjax@*/**/tex-chtml.js", stalled_first)
        self.goto(page, "index.html")
        page.locator("#paper-interchange-join-shortest-queue-rv .paper-abstract").evaluate("el => el.open = true")
        retry = page.get_by_role("button", name="Retry equations").first
        retry.wait_for()
        retry.click()
        page.wait_for_function("window.__mathCalls && __mathCalls.length > 0 && __mathActive === 0")
        self.assertEqual(len(attempts), 2)
        self.assertEqual(page.locator(".math-load-status").count(), 0)

    def test_touch_copy_uses_visible_button_and_correct_text(self):
        page = self.page(fixture=True, is_mobile=True, has_touch=True)
        page.add_init_script("""Object.defineProperty(navigator, 'clipboard', {value: {
            writeText: async function (text) { window.__copiedText = text; }
        }});""")
        self.goto(page, "blogs/2026-02-09-latex_style_guide.html")
        button = page.get_by_role("button", name="Copy code to clipboard").first
        expected = button.locator("..").locator("code").inner_text()
        button.tap()
        page.wait_for_function("expected => window.__copiedText === expected", arg=expected)
        self.assertEqual(button.inner_text(), "Copied")
        self.assert_fits(page, "touch code copying")

    def test_keyboard_scrolling_for_code_table_and_diagram(self):
        def scroll_region(page, region):
            region.wait_for()
            self.assertEqual(region.get_attribute("tabindex"), "0")
            self.assertEqual(region.get_attribute("role"), "region")
            self.assertTrue(region.get_attribute("aria-label"))
            region.evaluate("el => el.scrollLeft = 0")
            region.focus()
            page.keyboard.press("ArrowRight")
            page.wait_for_function("el => el.scrollLeft > 0", arg=region.element_handle())
            self.assertEqual(page.evaluate("scrollX"), 0)
            self.assert_fits(page, "keyboard local scrolling")

        # Existing posts currently have no HTML tables. Insert a wide table in
        # this isolated document response to exercise the future-content path.
        page = self.page(width=320, fixture=True)
        name = "blogs/2026-02-09-latex_style_guide.html"
        source = (ROOT / "dist" / name).read_text()
        marker = '<div class="post-body">'
        self.assertIn(marker, source)
        table = '<table><caption>Test comparison</caption><tr>' + ''.join(
            f'<th style="white-space:nowrap">Long comparison column {i}</th>' for i in range(4)
        ) + '</tr><tr><td>A</td><td>B</td><td>C</td><td>D</td></tr></table>'
        page.route(f"**/{name}", lambda route: route.fulfill(
            status=200, content_type="text/html", body=source.replace(marker, marker + table, 1)
        ))
        self.goto(page, name)
        scroll_region(page, page.locator("pre[data-scroll-label][tabindex='0']").first)
        scroll_region(page, page.locator(".table-scroll[tabindex='0']").first)
        self.assertEqual(page.locator(".table-scroll table").evaluate("el => getComputedStyle(el).display"), "table")

        diagram_page = self.page(width=320)
        self.goto(diagram_page, "blogs/2026-02-07-real_analysis.html")
        self.ready_content(diagram_page, "blogs/2026-02-07-real_analysis.html")
        scroll_region(diagram_page, diagram_page.locator("pre.mermaid"))

    def test_late_dependency_does_not_undo_reader_scroll(self):
        page = self.page(fixture=True, width=375, reduced_motion="reduce")
        page.route("**/mathjax@*/**/tex-chtml.js", lambda route: route.fulfill(
            status=200, content_type="text/javascript", headers={"access-control-allow-origin": "*"},
            body=(FIXTURES / "mathjax.js").read_text().replace(
                "promise: Promise.resolve()", "promise: new Promise(resolve => window.__finishMath = resolve)"
            ),
        ))
        self.goto(page, "blogs/2026-02-07-real_analysis.html#chapter-2-constructing-lebesgue-measure")
        page.wait_for_function("typeof window.__finishMath === 'function'")
        initial_y = page.evaluate("scrollY")
        page.mouse.wheel(0, 600)
        page.wait_for_function("before => scrollY > before + 250", arg=initial_y)
        reader_y = page.evaluate("scrollY")
        page.evaluate("window.__finishMath()")
        page.wait_for_function("window.__mathCalls && __mathCalls.length > 0 && __mathActive === 0")
        self.settle(page)
        self.assertLess(abs(page.evaluate("scrollY") - reader_y), 5,
                        "Finishing a dependency moved the reader back to the initial hash")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live-dependencies", action="store_true")
    args, remaining = parser.parse_known_args()
    LIVE = args.live_dependencies
    print("Dependency mode:", "REAL CDN (network required; no skips)" if LIVE else "LOCAL FIXTURES (behavior only)", flush=True)
    print(f"Viewport matrix: {len(PAGES)} pages × {len(WIDTHS)} widths × 2 themes = {len(PAGES) * len(WIDTHS) * 2} checks", flush=True)
    unittest.main(argv=[__file__, *remaining], verbosity=2)
