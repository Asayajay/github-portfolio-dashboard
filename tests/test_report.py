from datetime import datetime, timezone

from ghdash.health import compute_repo_health, summarize_portfolio
from ghdash.report import render_cli_report, render_markdown_report, write_markdown_report

FIXED_NOW = datetime(2026, 8, 20, tzinfo=timezone.utc)

REAL_README = """# My Project

This project does a genuinely useful thing and this sentence exists
purely to push the word count past the stub threshold so the check
actually passes, which is the whole point of writing this test.
"""


def healthy():
    return compute_repo_health(
        full_name="a/healthy",
        root_files=["README.md", "LICENSE", ".gitignore"],
        readme_content=REAL_README,
        gitignore_content="__pycache__/\n.venv/\n.env\ndist/\n",
        last_commit_date="2026-08-19T00:00:00Z",
        open_issue_count=1,
        now=FIXED_NOW,
    )


def unhealthy():
    return compute_repo_health(
        full_name="a/unhealthy",
        root_files=[],
        readme_content=None,
        gitignore_content=None,
        last_commit_date=None,
        open_issue_count=4,
        now=FIXED_NOW,
    )


def test_cli_report_includes_summary_line_and_both_repos():
    report = render_cli_report([healthy(), unhealthy()])
    assert "Scanned 2 repos" in report
    assert "a/healthy" in report
    assert "a/unhealthy" in report
    assert "No LICENSE file found." in report


def test_cli_report_marks_healthy_repo_with_checkmark():
    report = render_cli_report([healthy()])
    assert "✓ a/healthy" in report


def test_cli_report_marks_unhealthy_repo_with_x():
    report = render_cli_report([unhealthy()])
    assert "✗ a/unhealthy" in report


def test_markdown_report_has_summary_table_and_details_section():
    results = [healthy(), unhealthy()]
    summary = summarize_portfolio(results)
    markdown = render_markdown_report(results, summary, FIXED_NOW)

    assert "| Repo | LICENSE | README | .gitignore | Last commit | Open issues |" in markdown
    assert "## Details" in markdown
    assert "### a/unhealthy" in markdown
    # Fully healthy repos don't need a details section.
    assert "### a/healthy" not in markdown


def test_write_markdown_report_creates_timestamped_file(tmp_path):
    path = write_markdown_report([healthy()], tmp_path, generated_at=FIXED_NOW)
    assert path.exists()
    assert path.name == "portfolio-report-20260820-000000.md"
    assert "a/healthy" in path.read_text()


def stale():
    from ghdash.health import compute_repo_health

    return compute_repo_health(
        full_name="a/stale",
        root_files=["README.md", "LICENSE", ".gitignore"],
        readme_content=REAL_README,
        gitignore_content="__pycache__/\n.venv/\n.env\ndist/\n",
        last_commit_date="2023-01-01T00:00:00Z",
        open_issue_count=0,
        now=FIXED_NOW,
    )


def test_cli_report_tags_stale_repo():
    report = render_cli_report([stale()])
    assert "a/stale" in report
    assert "(stale)" in report


def test_cli_report_does_not_tag_fresh_repo_as_stale():
    report = render_cli_report([healthy()])
    assert "(stale)" not in report


def test_markdown_report_tags_stale_repo_in_table():
    results = [stale()]
    summary = summarize_portfolio(results)
    markdown = render_markdown_report(results, summary, FIXED_NOW)
    assert "(stale)" in markdown
