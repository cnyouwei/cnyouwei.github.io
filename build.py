#!/usr/bin/env python3
"""One-click website build from the JSON data in data/.

Usage:
    python3 build.py            # build the website into dist/
    python3 build.py --serve    # build, then preview at http://localhost:8000

The CV is NOT generated: the committed CV.pdf at the repository root is
copied into dist/ as-is.
"""

from __future__ import annotations

import argparse
import sys

from builder import checks, data, site


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serve", action="store_true", help="serve dist/ after building")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    try:
        everything = data.load_all()
    except data.DataError as exc:
        print(f"Data error: {exc}", file=sys.stderr)
        return 1

    site.build_site(everything)
    checks.check_site(everything)

    if args.serve:
        import functools
        import http.server

        from builder.config import DIST_DIR

        handler = functools.partial(
            http.server.SimpleHTTPRequestHandler, directory=str(DIST_DIR)
        )
        print(f"Serving {DIST_DIR} at http://localhost:{args.port} (Ctrl-C to stop)")
        http.server.ThreadingHTTPServer(("", args.port), handler).serve_forever()

    return 0


if __name__ == "__main__":
    sys.exit(main())
