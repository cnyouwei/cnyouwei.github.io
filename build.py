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
    parser.add_argument("--host", default="127.0.0.1", help="preview bind address (default: loopback only)")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")

    try:
        everything = data.load_all()
        site.build_site(everything)
        checks.check_site(everything)
    except (data.DataError, checks.CheckError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.serve:
        import functools
        import http.server

        from builder.config import DIST_DIR

        handler = functools.partial(
            http.server.SimpleHTTPRequestHandler, directory=str(DIST_DIR)
        )
        print(f"Serving {DIST_DIR} at http://{args.host}:{args.port} (Ctrl-C to stop)")
        http.server.ThreadingHTTPServer((args.host, args.port), handler).serve_forever()

    return 0


if __name__ == "__main__":
    sys.exit(main())
