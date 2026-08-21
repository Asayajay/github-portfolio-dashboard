"""Turns scan results into a CLI summary and a markdown report file."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from ghdash.health import PortfolioSummary, RepoHealth, summarize_portfolio


def _mark(passed: bool) -> str:
    return "✓" if passed else "✗"


def _recency_label(days: int | None) -> str:
    if days is None:
        return "no commits"
    if days == 0:
        return "today"
    if days == 1:
        return "1 day ago"
    return f"{days} days ago"


def render_cli_report(results: list[RepoHealth]) -> str:
    """Render a human-readable summary for terminal output."""
    summary = summarize_portfolio(results)
    lines = [
        f"Scanned {summary.repo_count} repos: {summary.fully_healthy_count} fully healthy "
        f"(all 3 hygiene checks), average hygiene {summary.average_hygiene_percent}%, "
        f"{summary.total_open_issues} open issues total",
        "",
    ]

    for result in sorted(results, key=lambda r: r.full_name.lower()):
        lines.append(
            f"{_mark(result.hygiene_score == 3)} {result.full_name} "
            f"[{result.hygiene_score}/3] "
            f"last commit {_recency_label(result.days_since_last_commit)}, "
            f"{result.open_issue_count} open issues"
        )
        for issue in result.hygiene_issues:
            lines.append(f"    - {issue}")

    return "\n".join(lines)


def render_markdown_report(
    results: list[RepoHealth], summary: PortfolioSummary, generated_at: datetime
) -> str:
    """Render the same results as a markdown file, with a summary table up top."""
    sorted_results = sorted(results, key=lambda r: r.full_name.lower())

    lines = [
        "# GitHub Portfolio Dashboard",
        "",
        f"Generated {generated_at.strftime('%Y-%m-%d %H:%M UTC')}",
        f"Scanned {summary.repo_count} repos: {summary.fully_healthy_count} fully healthy, "
        f"average hygiene {summary.average_hygiene_percent}%, "
        f"{summary.total_open_issues} open issues total.",
        "",
        "| Repo | LICENSE | README | .gitignore | Last commit | Open issues |",
        "| --- | --- | --- | --- | --- | --- |",
    ]

    for result in sorted_results:
        lines.append(
            "| "
            + " | ".join(
                [
                    result.full_name,
                    _mark(result.license_ok),
                    _mark(result.readme_ok),
                    _mark(result.gitignore_ok),
                    _recency_label(result.days_since_last_commit),
                    str(result.open_issue_count),
                ]
            )
            + " |"
        )

    lines += ["", "## Details", ""]

    for result in sorted_results:
        if result.hygiene_score == 3:
            continue
        lines.append(f"### {result.full_name}")
        lines.extend(f"- {issue}" for issue in result.hygiene_issues)
        lines.append("")

    return "\n".join(lines)


def write_markdown_report(
    results: list[RepoHealth], output_dir: Path, generated_at: datetime | None = None
) -> Path:
    """Write the markdown report to `output_dir`, timestamped, and return its path."""
    generated_at = generated_at or datetime.now(timezone.utc)
    summary = summarize_portfolio(results)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"portfolio-report-{generated_at.strftime('%Y%m%d-%H%M%S')}.md"
    output_path.write_text(render_markdown_report(results, summary, generated_at))
    return output_path
