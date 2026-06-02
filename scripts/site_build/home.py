from __future__ import annotations

from .common import INDEX_PATH
from .page_context import build_base_context
from .template_engine import render_template
from .templates import mathjax_config_script


def home_page_template(
    *,
    ga_id: str,
    selected_papers_html: str,
    research_content_html: str,
    teaching_home_content_html: str,
    recent_posts_html: str,
) -> str:
    main_html = render_template(
        "pages/home.html.j2",
        {
            "selected_papers_html": selected_papers_html,
            "research_content_html": research_content_html,
            "teaching_home_content_html": teaching_home_content_html,
            "recent_posts_html": recent_posts_html,
        },
    )

    return render_template(
        "base.html.j2",
        build_base_context(
            ga_id=ga_id,
            page_id="home",
            page_title="Wei You",
            meta_description=(
                "Wei You - Assistant Professor at HKUST. Research in stochastic models, "
                "queueing theory, applied probability, and sequential decision-making."
            ),
            include_cn_fonts=True,
            css_href="css/site.css",
            js_prefix="js/",
            brand_href="#home",
            brand_aria_label="Go to home",
            home_href="#home",
            research_href="#research",
            talks_href="#talks",
            teaching_href="#teaching",
            team_href="#team",
            about_href="#about",
            blog_href="#blog",
            main_html=main_html,
            page_scripts=["pages/research.js"],
            # Config only: the home page has math solely inside collapsed paper
            # abstracts, so research.js loads the MathJax engine on first open
            # and typesets each abstract as it is revealed.
            extra_before_scripts_html=mathjax_config_script(
                include_chtml=False, with_loader=False, autotypeset=False
            ),
        ),
    )


def build_home(
    *,
    ga_id: str,
    selected_papers_html: str,
    research_content_html: str,
    teaching_home_content_html: str,
    recent_posts_html: str,
) -> None:
    html = home_page_template(
        ga_id=ga_id,
        selected_papers_html=selected_papers_html,
        research_content_html=research_content_html,
        teaching_home_content_html=teaching_home_content_html,
        recent_posts_html=recent_posts_html,
    )
    INDEX_PATH.write_text(html, encoding="utf-8")
    print("Updated: index.html")
