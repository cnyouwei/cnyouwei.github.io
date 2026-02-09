#!/usr/bin/env python3
"""Snapshot and verify generated site artifacts for parity checks."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
INDEX_PATH = ROOT_DIR / "index.html"

MARKER_PAIRS = {
    "selected_papers": ("<!-- SELECTED-PAPERS:START -->", "<!-- SELECTED-PAPERS:END -->"),
    "research_content": ("<!-- RESEARCH-CONTENT:START -->", "<!-- RESEARCH-CONTENT:END -->"),
    "nav_teaching_dropdown": (
        "<!-- NAV-TEACHING-DROPDOWN:START -->",
        "<!-- NAV-TEACHING-DROPDOWN:END -->",
    ),
    "nav_blog_dropdown": ("<!-- NAV-BLOG-DROPDOWN:START -->", "<!-- NAV-BLOG-DROPDOWN:END -->"),
}


def digest_file(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest()


def generated_files() -> list[Path]:
    files = [INDEX_PATH]
    files.extend(sorted((ROOT_DIR / "blogs").glob("*.html")))
    files.extend(sorted((ROOT_DIR / "teaching").glob("*.html")))
    files.append(ROOT_DIR / "blogs" / "posts.json")
    files.append(ROOT_DIR / "blogs" / "posts.js")
    # De-duplicate and keep stable ordering.
    uniq = sorted({path.resolve() for path in files if path.exists()})
    return [Path(path) for path in uniq]


def marker_bodies(index_text: str) -> dict[str, str | None]:
    bodies: dict[str, str | None] = {}
    for key, (start_marker, end_marker) in MARKER_PAIRS.items():
        pattern = re.compile(
            (
                rf"^(?P<indent>[ \t]*){re.escape(start_marker)}\n"
                rf"(?P<body>.*?)(?P=indent){re.escape(end_marker)}"
            ),
            re.DOTALL | re.MULTILINE,
        )
        match = pattern.search(index_text)
        if not match:
            bodies[key] = None
            continue
        bodies[key] = match.group("body")
    return bodies


def build_snapshot() -> dict[str, Any]:
    paths = generated_files()
    index_text = INDEX_PATH.read_text(encoding="utf-8")
    return {
        "files": {
            str(path.relative_to(ROOT_DIR)): {
                "sha256": digest_file(path),
                "size": path.stat().st_size,
            }
            for path in paths
        },
        "markers": marker_bodies(index_text),
    }


def write_snapshot(output_path: Path) -> int:
    snapshot = build_snapshot()
    output_path.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote snapshot: {output_path}")
    print(f"Tracked files: {len(snapshot['files'])}")
    return 0


def compare_snapshots(baseline: dict[str, Any], current: dict[str, Any]) -> int:
    errors: list[str] = []

    baseline_files = baseline.get("files", {})
    current_files = current.get("files", {})
    if not isinstance(baseline_files, dict) or not isinstance(current_files, dict):
        print("Invalid snapshot format: expected `files` object.", file=sys.stderr)
        return 2

    baseline_set = set(baseline_files.keys())
    current_set = set(current_files.keys())

    missing = sorted(baseline_set - current_set)
    extra = sorted(current_set - baseline_set)
    for item in missing:
        errors.append(f"Missing generated file: {item}")
    for item in extra:
        errors.append(f"Unexpected generated file: {item}")

    shared = sorted(baseline_set & current_set)
    for rel_path in shared:
        base_hash = baseline_files[rel_path].get("sha256")
        curr_hash = current_files[rel_path].get("sha256")
        if base_hash != curr_hash:
            errors.append(f"Hash mismatch: {rel_path}\n  baseline={base_hash}\n  current={curr_hash}")

    baseline_markers = baseline.get("markers", {})
    current_markers = current.get("markers", {})
    if not isinstance(baseline_markers, dict) or not isinstance(current_markers, dict):
        print("Invalid snapshot format: expected `markers` object.", file=sys.stderr)
        return 2

    for marker in sorted(MARKER_PAIRS):
        base_body = baseline_markers.get(marker)
        curr_body = current_markers.get(marker)
        if base_body is None:
            errors.append(f"Baseline snapshot missing marker block: {marker}")
            continue
        if curr_body is None:
            errors.append(f"Current output missing marker block: {marker}")
            continue
        if base_body != curr_body:
            errors.append(f"Marker block mismatch: {marker}")

    if errors:
        print("Parity check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Parity check passed: generated artifacts and marker blocks match baseline.")
    return 0


def check_snapshot(baseline_path: Path) -> int:
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    current = build_snapshot()
    return compare_snapshots(baseline, current)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    snapshot_parser = subparsers.add_parser("snapshot", help="Write current generated snapshot.")
    snapshot_parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path to write snapshot JSON.",
    )

    check_parser = subparsers.add_parser("check", help="Compare current outputs to baseline.")
    check_parser.add_argument(
        "--baseline",
        required=True,
        type=Path,
        help="Path to baseline snapshot JSON.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "snapshot":
        return write_snapshot(args.output)
    if args.command == "check":
        return check_snapshot(args.baseline)
    print(f"Unknown command: {args.command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
