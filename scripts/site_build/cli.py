from __future__ import annotations

from .blog import build_blog, read_source_posts
from .research import build_research
from .teaching import build_teaching, load_teaching_data


def main() -> None:
    print("[1/3] Building research section...")
    build_research()
    posts = read_source_posts()
    courses = load_teaching_data()
    print("[2/3] Building blog...")
    build_blog(posts)
    print("[3/3] Building teaching pages...")
    build_teaching(courses)
    print("Site build complete.")
