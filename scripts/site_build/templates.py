from __future__ import annotations

BASE_FONT_FAMILIES = [
    "Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700",
    "Space+Grotesk:wght@400;500;600;700",
    "Rajdhani:wght@500;600;700",
    "Orbitron:wght@500;600;700",
    "Source+Sans+3:wght@400;500;600;700",
    "Merriweather:wght@400;700",
]
CN_FONT_FAMILIES = [
    "Noto+Sans+SC:wght@400;500;700",
]


def _google_fonts_href(families: list[str]) -> str:
    query = "&amp;".join(f"family={family}" for family in families)
    return f"https://fonts.googleapis.com/css2?{query}&amp;display=swap"


def font_stylesheet_href(*, include_cn: bool = False) -> str:
    families = list(BASE_FONT_FAMILIES)
    if include_cn:
        families.extend(CN_FONT_FAMILIES)
    return _google_fonts_href(families)


def theme_bootstrap_script() -> str:
    return """  <script>
    (function () {
      try {
        var storedTheme = localStorage.getItem('wy-theme');
        var themeSource = localStorage.getItem('wy-theme-source');
        if (
          themeSource === 'manual' &&
          (storedTheme === 'cyberpunk' || storedTheme === 'solarized')
        ) {
          document.documentElement.setAttribute('data-theme', storedTheme);
        }
      } catch (error) {}
    })();
  </script>"""


def mathjax_config_script(*, include_chtml: bool) -> str:
    chtml_block = (
        "      chtml: {\n"
        "        mtextInheritFont: true,\n"
        "        merrorInheritFont: true\n"
        "      },\n"
        if include_chtml
        else ""
    )
    return f"""  <script>
    window.MathJax = {{
      tex: {{
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
  </script>
  <script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>"""
