from __future__ import annotations


def font_stylesheet_href(*, include_cn: bool = False) -> str:
    if include_cn:
        return (
            "https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700"
            "&amp;family=Space+Grotesk:wght@400;500;600;700"
            "&amp;family=Rajdhani:wght@500;600;700"
            "&amp;family=Orbitron:wght@500;600;700"
            "&amp;family=Source+Sans+3:wght@400;500;600;700"
            "&amp;family=Merriweather:wght@400;700"
            "&amp;family=Noto+Sans+SC:wght@400;500;700&amp;display=swap"
        )
    return (
        "https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700"
        "&amp;family=Space+Grotesk:wght@400;500;600;700"
        "&amp;family=Rajdhani:wght@500;600;700"
        "&amp;family=Orbitron:wght@500;600;700"
        "&amp;family=Source+Sans+3:wght@400;500;600;700"
        "&amp;family=Merriweather:wght@400;700&amp;display=swap"
    )


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
    if include_chtml:
        return """  <script>
    window.MathJax = {
      tex: {
        inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
        displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
        processEscapes: true,
        macros: {
          bm: ['\\\\boldsymbol{#1}', 1]
        }
      },
      chtml: {
        mtextInheritFont: true,
        merrorInheritFont: true
      },
      options: {
        skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code']
      }
    };
  </script>
  <script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>"""


    return """  <script>
    window.MathJax = {
      tex: {
        inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
        displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
        processEscapes: true,
        macros: {
          bm: ['\\\\boldsymbol{#1}', 1]
        }
      },
      options: {
        skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code']
      }
    };
  </script>
  <script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>"""
