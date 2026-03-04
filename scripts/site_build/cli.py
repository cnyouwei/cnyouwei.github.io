from __future__ import annotations

from .blog import build_blog, read_source_posts
from .home import build_home
from .research import render_research_sections
from .teaching import build_teaching, load_teaching_data, render_home_teaching_markup


def main() -> None:
    print("[1/4] Building research section...")
    research_payload = render_research_sections()
    paper_count = int(research_payload["paper_count"])
    print(f"Built research section from {paper_count} entries.")
    posts = read_source_posts()
    courses = load_teaching_data()
    print("[2/4] Building blog...")
    build_blog(posts)
    print("[3/4] Building teaching pages...")
    build_teaching(courses)
    print("[4/4] Building home page...")
    build_home(
        selected_papers_html=str(research_payload["selected_markup"]),
        research_content_html=str(research_payload["research_markup"]),
        teaching_home_content_html=render_home_teaching_markup(courses),
    )
    print("Site build complete.")
