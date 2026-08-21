from datetime import datetime, timezone

from ghdash.health import compute_repo_health, summarize_portfolio

REAL_README = """# My Project

This project does a genuinely useful thing and this sentence exists
purely to push the word count past the stub threshold so the check
actually passes, which is the whole point of writing this test.
"""

FULL_GITIGNORE = "__pycache__/\n*.pyc\n.venv/\n.env\ndist/\nbuild/\n"

FIXED_NOW = datetime(2026, 8, 20, tzinfo=timezone.utc)


def healthy_repo(full_name="a/repo", last_commit_date="2026-08-01T00:00:00Z", open_issues=2):
    return compute_repo_health(
        full_name=full_name,
        root_files=["README.md", "LICENSE", ".gitignore"],
        readme_content=REAL_README,
        gitignore_content=FULL_GITIGNORE,
        last_commit_date=last_commit_date,
        open_issue_count=open_issues,
        now=FIXED_NOW,
    )


def test_fully_healthy_repo_scores_three_of_three():
    result = healthy_repo()
    assert result.license_ok and result.readme_ok and result.gitignore_ok
    assert result.hygiene_score == 3
    assert result.hygiene_percent == 100.0
    assert result.hygiene_issues == []


def test_missing_everything_scores_zero():
    result = compute_repo_health(
        full_name="a/bare",
        root_files=[],
        readme_content=None,
        gitignore_content=None,
        last_commit_date=None,
        open_issue_count=0,
        now=FIXED_NOW,
    )
    assert result.hygiene_score == 0
    assert result.hygiene_percent == 0.0
    assert len(result.hygiene_issues) == 3


def test_partial_hygiene_scores_partial_credit():
    result = compute_repo_health(
        full_name="a/partial",
        root_files=["README.md", "LICENSE"],
        readme_content=REAL_README,
        gitignore_content=None,
        last_commit_date="2026-01-01T00:00:00Z",
        open_issue_count=0,
        now=FIXED_NOW,
    )
    assert result.hygiene_score == 2
    assert round(result.hygiene_percent, 1) == 66.7
    assert not result.gitignore_ok


def test_days_since_last_commit_computed_correctly():
    result = healthy_repo(last_commit_date="2026-08-01T00:00:00Z")
    # Aug 1 -> Aug 20 is 19 days.
    assert result.days_since_last_commit == 19


def test_days_since_last_commit_none_for_empty_repo():
    result = compute_repo_health(
        full_name="a/empty",
        root_files=[],
        readme_content=None,
        gitignore_content=None,
        last_commit_date=None,
        open_issue_count=0,
        now=FIXED_NOW,
    )
    assert result.days_since_last_commit is None


def test_open_issue_count_passes_through():
    result = healthy_repo(open_issues=7)
    assert result.open_issue_count == 7


def test_summarize_portfolio_empty_list():
    summary = summarize_portfolio([])
    assert summary.repo_count == 0
    assert summary.average_hygiene_percent == 0.0


def test_summarize_portfolio_rolls_up_correctly():
    results = [
        healthy_repo(full_name="a/healthy", open_issues=1),
        compute_repo_health(
            full_name="a/no-license",
            root_files=["README.md", ".gitignore"],
            readme_content=REAL_README,
            gitignore_content=FULL_GITIGNORE,
            last_commit_date="2026-08-01T00:00:00Z",
            open_issue_count=3,
            now=FIXED_NOW,
        ),
        compute_repo_health(
            full_name="a/bare",
            root_files=[],
            readme_content=None,
            gitignore_content=None,
            last_commit_date=None,
            open_issue_count=0,
            now=FIXED_NOW,
        ),
    ]
    summary = summarize_portfolio(results)

    assert summary.repo_count == 3
    assert summary.fully_healthy_count == 1
    assert summary.total_open_issues == 4
    assert summary.repos_missing_license == ["a/no-license", "a/bare"]
    assert summary.repos_missing_readme == ["a/bare"]
    assert summary.repos_missing_gitignore == ["a/bare"]
    # (100 + 66.7 + 0) / 3 = 55.57 -> rounds to 55.6
    assert summary.average_hygiene_percent == 55.6


def test_repo_untouched_past_threshold_is_flagged_stale():
    result = compute_repo_health(
        full_name="a/old",
        root_files=["README.md", "LICENSE", ".gitignore"],
        readme_content=REAL_README,
        gitignore_content=FULL_GITIGNORE,
        last_commit_date="2024-01-01T00:00:00Z",
        open_issue_count=0,
        now=FIXED_NOW,
        stale_after_days=365,
    )
    assert result.is_stale is True
    # Staleness is informational only -- doesn't touch the hygiene score.
    assert result.hygiene_score == 3


def test_recently_touched_repo_is_not_stale():
    result = healthy_repo(last_commit_date="2026-08-01T00:00:00Z")
    assert result.is_stale is False


def test_repo_with_no_commits_is_not_flagged_stale():
    # No commit history isn't the same claim as "hasn't been touched in a
    # while" -- there's nothing to measure recency against.
    result = compute_repo_health(
        full_name="a/empty",
        root_files=[],
        readme_content=None,
        gitignore_content=None,
        last_commit_date=None,
        open_issue_count=0,
        now=FIXED_NOW,
    )
    assert result.is_stale is False


def test_stale_threshold_is_configurable():
    result = compute_repo_health(
        full_name="a/recentish",
        root_files=["README.md", "LICENSE", ".gitignore"],
        readme_content=REAL_README,
        gitignore_content=FULL_GITIGNORE,
        last_commit_date="2026-06-01T00:00:00Z",
        open_issue_count=0,
        now=FIXED_NOW,
        stale_after_days=60,
    )
    assert result.is_stale is True


def test_summarize_portfolio_counts_stale_repos():
    results = [
        healthy_repo(full_name="a/fresh", last_commit_date="2026-08-01T00:00:00Z"),
        compute_repo_health(
            full_name="a/old",
            root_files=["README.md", "LICENSE", ".gitignore"],
            readme_content=REAL_README,
            gitignore_content=FULL_GITIGNORE,
            last_commit_date="2023-01-01T00:00:00Z",
            open_issue_count=0,
            now=FIXED_NOW,
        ),
    ]
    summary = summarize_portfolio(results)
    assert summary.stale_count == 1
