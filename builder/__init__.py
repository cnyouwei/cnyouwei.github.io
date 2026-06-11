"""Static site generator for cnyouwei.github.io.

Everything renders from the JSON files in data/ (and markdown in data/blog/):

    data/*.json + data/blog/*.md --> builder.site --> dist/

The CV is not generated; the committed CV.pdf at the repository root is
copied into dist/ verbatim. Public entry point: build.py at the repo root.
"""

__all__ = ["config", "data", "markdown", "render", "site", "checks"]
