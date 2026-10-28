"""Command-line interface for the readiness auditor."""

from __future__ import annotations

import argparse
import os
import sys

from . import __version__
from .checks import CHECK_IDS, run_checks
from .report import render_json, render_markdown, score_results
from .scanner import scan_project


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="readiness-audit",
        description="Audit an LLM project folder for production readiness.",
    )
    parser.add_argument("--path", help="Project directory to audit")
    parser.add_argument("--out", default="readiness-report",
                        help="Directory for report.json and report.md (default: readiness-report)")
    parser.add_argument("--list-checks", action="store_true",
                        help="List check ids and exit")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--exclude", action="append", default=None,
                        help="Glob pattern to exclude from scanning (repeatable)")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    if args.list_checks:
        for check_id in CHECK_IDS:
            print(check_id)
        return 0

    if not args.path:
        print("error: --path is required unless --list-checks is given", file=sys.stderr)
        return 2

    try:
        scan = scan_project(args.path, exclude=args.exclude)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    results = run_checks(scan)
    score, verdict, _areas = score_results(results)

    try:
        os.makedirs(args.out, exist_ok=True)
        with open(os.path.join(args.out, "report.json"), "w", encoding="utf-8") as handle:
            handle.write(render_json(args.path, results, score, verdict))
        with open(os.path.join(args.out, "report.md"), "w", encoding="utf-8") as handle:
            handle.write(render_markdown(args.path, results, score, verdict))
    except OSError as exc:
        print(f"error: cannot write report to {args.out!r}: {exc}", file=sys.stderr)
        return 2

    passed = sum(1 for r in results if r.status == "pass")
    print(f"Score: {score:.1f}% ({passed}/{len(results)})")
    print(f"Verdict: {verdict}")
    print(f"Report: {args.out}/report.md, {args.out}/report.json")
    return 0 if verdict in ("GO", "CONDITIONAL GO") else 1
