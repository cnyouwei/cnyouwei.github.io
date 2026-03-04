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

INDEX_CONTRACT_PATTERNS = {
    "home_page_attr": r'<html\b[^>]*\bdata-page="home"',
    "ga_attr": r'<html\b[^>]*\bdata-ga-id="[^"]+"',
    "section_home": r'<section\b[^>]*\bid="home"',
    "section_research": r'<section\b[^>]*\bid="research"',
    "section_talks": r'<section\b[^>]*\bid="talks"',
    "section_teaching": r'<section\b[^>]*\bid="teaching"',
    "section_team": r'<section\b[^>]*\bid="team"',
    "section_about": r'<section\b[^>]*\bid="about"',
    "section_blog": r'<section\b[^>]*\bid="blog"',
    "recent_posts_mount": r'<div\b[^>]*\bid="recentPosts"',
    "mathjax_config": r"window\.MathJax\s*=",
    "research_page_script": r'<script[^>]*\bsrc="js/pages/research\.js"[^>]*>',
    "back_to_top_button": r'<button\b[^>]*\bclass="back-to-top"',
    "clustrmaps": r'<script[^>]*\bid=["\']clustrmaps["\']',
}


def digest_file(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest()


def generated_files() -> list[Path]:
    files = [INDEX_PATH]
    files.extend(sorted((ROOT_DIR / "blogs").glob("*.html")))
    files.extend(sorted((ROOT_DIR / "teaching").glob("*.html")))
    uniq = sorted({path.resolve() for path in files if path.exists()})
    return [Path(path) for path in uniq]


def index_contract_flags(index_text: str) -> dict[str, bool]:
    return {
        key: bool(re.search(pattern, index_text, flags=re.IGNORECASE | re.MULTILINE))
        for key, pattern in INDEX_CONTRACT_PATTERNS.items()
    }


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
        "index_contract": index_contract_flags(index_text),
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

    baseline_contract = baseline.get("index_contract", {})
    current_contract = current.get("index_contract", {})
    if not isinstance(baseline_contract, dict) or not isinstance(current_contract, dict):
        print("Invalid snapshot format: expected `index_contract` object.", file=sys.stderr)
        return 2

    for key in sorted(INDEX_CONTRACT_PATTERNS):
        base_flag = bool(baseline_contract.get(key, False))
        curr_flag = bool(current_contract.get(key, False))
        if base_flag != curr_flag:
            errors.append(
                f"Index contract mismatch: {key}\n  baseline={base_flag}\n  current={curr_flag}"
            )

    if errors:
        print("Parity check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Parity check passed: generated artifacts and index contract match baseline.")
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
