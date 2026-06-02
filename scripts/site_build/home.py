from __future__ import annotations

from .common import INDEX_PATH, page_context
from .template_engine import render_template


def build_home(
    *,
    ga_id: str,
    selected_papers_html: str,
    research_content_html: str,
    teaching_home_content_html: str,
    recent_posts_html: str,
) -> None:
    main_html = render_template(
        "pages/home.html.j2",
        {
            "selected_papers_html": selected_papers_html,
            "research_content_html": research_content_html,
            "teaching_home_content_html": teaching_home_content_html,
            "recent_posts_html": recent_posts_html,
        },
    )

    html = render_template(
        "base.html.j2",
        page_context(
            ga_id=ga_id,
            page_id="home",
            page_title="Wei You",
            meta_description=(
                "Wei You - Assistant Professor at HKUST. Research in stochastic models, "
                "queueing theory, applied probability, and sequential decision-making."
            ),
            main_html=main_html,
            subpage=False,
            # Home math lives only inside collapsed paper abstracts, so research.js
            # loads the MathJax engine on first open rather than up front.
            mathjax="lazy",
            page_scripts=["pages/research.js"],
        ),
    )
    INDEX_PATH.write_text(html, encoding="utf-8")
    print("Updated: index.html")
