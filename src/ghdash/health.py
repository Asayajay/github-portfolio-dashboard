"""Per-repo health rollup and account-wide portfolio summary.

Deliberate design choice: "days since last commit" and "open issue count"
are reported as plain informational signals, not folded into the health
score. A finished personal project that hasn't been touched in a year
isn't unhealthy just because it's quiet -- staleness only matters alongside
missing hygiene basics, which is what the score actually measures. Folding
recency into the score would penalize exactly the kind of project (done,
stable, no reason to keep committing) that this account has plenty of.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from ghdash.checks import check_gitignore, check_license, check_readme


@dataclass
class RepoHealth:
    full_name: str
    license_ok: bool
    readme_ok: bool
    gitignore_ok: bool
    hygiene_issues: list[str]
    hygiene_score: int  # 0-3, number of hygiene checks passed
    hygiene_percent: float  # hygiene_score / 3 as a percentage
    last_commit_date: str | None
    days_since_last_commit: int | None
    open_issue_count: int


@dataclass
class PortfolioSummary:
    repo_count: int
    fully_healthy_count: int
    average_hygiene_percent: float
    total_open_issues: int
    repos_missing_license: list[str] = field(default_factory=list)
    repos_missing_readme: list[str] = field(default_factory=list)
    repos_missing_gitignore: list[str] = field(default_factory=list)


def _parse_days_since(last_commit_date: str | None, now: datetime) -> int | None:
    if not last_commit_date:
        return None
    commit_dt = datetime.fromisoformat(last_commit_date.replace("Z", "+00:00"))
    return (now - commit_dt).days


def compute_repo_health(
    full_name: str,
    root_files: list[str],
    readme_content: str | None,
    gitignore_content: str | None,
    last_commit_date: str | None,
    open_issue_count: int,
    now: datetime | None = None,
) -> RepoHealth:
    now = now or datetime.now(timezone.utc)

    license_result = check_license(root_files)
    readme_result = check_readme(root_files, readme_content)
    gitignore_result = check_gitignore(root_files, gitignore_content)

    hygiene_issues = license_result.issues + readme_result.issues + gitignore_result.issues
    hygiene_score = sum(
        [license_result.passed, readme_result.passed, gitignore_result.passed]
    )

    return RepoHealth(
        full_name=full_name,
        license_ok=license_result.passed,
        readme_ok=readme_result.passed,
        gitignore_ok=gitignore_result.passed,
        hygiene_issues=hygiene_issues,
        hygiene_score=hygiene_score,
        hygiene_percent=round(hygiene_score / 3 * 100, 1),
        last_commit_date=last_commit_date,
        days_since_last_commit=_parse_days_since(last_commit_date, now),
        open_issue_count=open_issue_count,
    )


def summarize_portfolio(results: list[RepoHealth]) -> PortfolioSummary:
    if not results:
        return PortfolioSummary(
            repo_count=0, fully_healthy_count=0, average_hygiene_percent=0.0, total_open_issues=0
        )

    average_hygiene_percent = round(
        sum(r.hygiene_percent for r in results) / len(results), 1
    )

    return PortfolioSummary(
        repo_count=len(results),
        fully_healthy_count=sum(1 for r in results if r.hygiene_score == 3),
        average_hygiene_percent=average_hygiene_percent,
        total_open_issues=sum(r.open_issue_count for r in results),
        repos_missing_license=[r.full_name for r in results if not r.license_ok],
        repos_missing_readme=[r.full_name for r in results if not r.readme_ok],
        repos_missing_gitignore=[r.full_name for r in results if not r.gitignore_ok],
    )
