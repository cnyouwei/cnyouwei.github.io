from __future__ import annotations

from .blog import build_blog, read_source_posts
from .nav import recent_posts_for_nav, update_index_nav_dropdowns
from .research import build_research
from .teaching import build_teaching, load_teaching_data


def main() -> None:
    print("[1/3] Building research section...")
    build_research()
    posts = read_source_posts()
    courses = load_teaching_data()
    recent_posts = recent_posts_for_nav(posts)
    print("[2/3] Building blog...")
    build_blog(posts, courses)
    print("[3/3] Building teaching pages...")
    build_teaching(courses, recent_posts)
    update_index_nav_dropdowns(posts, courses)
    print("Updated: index navigation dropdowns.")
    print("Site build complete.")
