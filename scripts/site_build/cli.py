from __future__ import annotations

from .blog import build_blog, read_source_posts, render_recent_posts_markup
from .common import read_ga_measurement_id
from .home import build_home
from .research import render_research_sections
from .teaching import build_teaching, load_teaching_data, render_home_teaching_markup


def main() -> None:
    ga_id = read_ga_measurement_id()
    print("[1/4] Building research section...")
    research_payload = render_research_sections()
    paper_count = int(research_payload["paper_count"])
    print(f"Built research section from {paper_count} entries.")
    posts = read_source_posts()
    recent_posts_html = render_recent_posts_markup(posts)
    courses = load_teaching_data()
    print("[2/4] Building blog...")
    build_blog(posts, ga_id)
    print("[3/4] Building teaching pages...")
    build_teaching(courses, ga_id)
    print("[4/4] Building home page...")
    build_home(
        ga_id=ga_id,
        selected_papers_html=str(research_payload["selected_markup"]),
        research_content_html=str(research_payload["research_markup"]),
        teaching_home_content_html=render_home_teaching_markup(courses),
        recent_posts_html=recent_posts_html,
    )
    print("Site build complete.")
