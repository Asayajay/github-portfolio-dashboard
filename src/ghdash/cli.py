"""Command-line entry point for the dashboard."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ghdash.github_client import GitHubClient
from ghdash.report import render_cli_report, write_markdown_report
from ghdash.scanner import scan_account


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ghdash",
        description="Live health dashboard for every repo in a GitHub account.",
    )
    parser.add_argument("--user", help="Scan someone else's public repos instead of your own.")
    parser.add_argument("--include-forks", action="store_true")
    parser.add_argument("--include-archived", action="store_true")
    parser.add_argument(
        "--output-dir",
        default="reports",
        help="Directory to write the timestamped markdown report to (default: reports/).",
    )
    parser.add_argument(
        "--no-report-file", action="store_true", help="Print to the terminal only, skip the file."
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        client = GitHubClient()
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    results = scan_account(
        client,
        owner=args.user,
        include_forks=args.include_forks,
        include_archived=args.include_archived,
    )

    print(render_cli_report(results))

    if not args.no_report_file:
        report_path = write_markdown_report(results, Path(args.output_dir))
        print(f"\nWrote {report_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
