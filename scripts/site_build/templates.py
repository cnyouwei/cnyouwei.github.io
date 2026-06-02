from __future__ import annotations

# Only the families actually referenced in css/site.css: Fraunces drives the
# serif headings, Google Sans Flex the body/UI. Add a family here only when a
# CSS rule uses it -- every entry is a render-blocking download.
BASE_FONT_FAMILIES = [
    "Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700",
    "Google+Sans+Flex:opsz,wght@8..144,400..700",
]
CN_FONT_FAMILIES = [
    "Noto+Sans+SC:wght@400;700",
]
# The only CJK text on the site is the name "尤为"; subset to those glyphs so
# the browser fetches ~2 glyphs instead of a full CJK face. URL-encoded UTF-8.
CN_FONT_SUBSET_TEXT = "%E5%B0%A4%E4%B8%BA"


def _google_fonts_href(families: list[str], *, text: str = "") -> str:
    query = "&amp;".join(f"family={family}" for family in families)
    if text:
        query += f"&amp;text={text}"
    return f"https://fonts.googleapis.com/css2?{query}&amp;display=swap"


def font_stylesheet_href() -> str:
    return _google_fonts_href(BASE_FONT_FAMILIES)


def cn_font_stylesheet_href() -> str:
    return _google_fonts_href(CN_FONT_FAMILIES, text=CN_FONT_SUBSET_TEXT)


def theme_bootstrap_script() -> str:
    return """  <script>
    (function () {
      try {
        var root = document.documentElement;
        var storedTheme = localStorage.getItem('wy-theme');
        var themeSource = localStorage.getItem('wy-theme-source');
        if (themeSource === 'manual' && (storedTheme === 'light' || storedTheme === 'dark')) {
          root.setAttribute('data-theme', storedTheme);
          return;
        }
        var prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        root.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
      } catch (error) {
        document.documentElement.setAttribute('data-theme', 'light');
      }
    })();
  </script>"""


MATHJAX_LOADER_SRC = "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"


def mathjax_config_script(
    *, include_chtml: bool, with_loader: bool = True, autotypeset: bool = True
) -> str:
    """Emit the MathJax config block.

    When ``with_loader`` is False the heavy ``tex-chtml.js`` script tag is
    omitted -- the page declares the config but defers the ~1 MB download to
    runtime (see js/pages/research.js, which loads it on first abstract open).

    When ``autotypeset`` is False, MathJax does not typeset on startup; the
    caller typesets each element as it becomes visible (collapsed abstracts are
    ``display:none`` and would otherwise be measured incorrectly).
    """
    chtml_block = (
        "      chtml: {\n"
        "        mtextInheritFont: true,\n"
        "        merrorInheritFont: true\n"
        "      },\n"
        if include_chtml
        else ""
    )
    startup_block = "" if autotypeset else "      startup: {\n        typeset: false\n      },\n"
    loader = f'\n  <script defer src="{MATHJAX_LOADER_SRC}"></script>' if with_loader else ""
    return f"""  <script>
    window.MathJax = {{
{startup_block}      tex: {{
        inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
        displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
        processEscapes: true,
        macros: {{
          bm: ['\\\\boldsymbol{{#1}}', 1]
        }}
      }},
{chtml_block}      options: {{
        skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code']
      }}
    }};
  </script>{loader}"""
