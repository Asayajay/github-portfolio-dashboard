"""Ties the GitHub client and the health rollup together into per-repo results."""

from __future__ import annotations

from datetime import datetime

from ghdash.checks import find_readme_filename
from ghdash.github_client import GitHubClient
from ghdash.health import RepoHealth, compute_repo_health


def scan_repo(client: GitHubClient, repo: dict, now: datetime | None = None) -> RepoHealth:
    """Pull everything needed to score a single repo's health."""
    full_name = repo["full_name"]
    ref = repo["default_branch"]
    root_files = client.list_root_contents(full_name, ref)

    readme_filename = find_readme_filename(root_files)
    readme_content = (
        client.get_file_content(full_name, readme_filename, ref) if readme_filename else None
    )

    gitignore_present = any(name.lower() == ".gitignore" for name in root_files)
    gitignore_content = (
        client.get_file_content(full_name, ".gitignore", ref) if gitignore_present else None
    )

    last_commit_date = client.get_latest_commit_date(full_name, ref)
    open_issue_count = client.get_open_issue_count(repo)

    return compute_repo_health(
        full_name=full_name,
        root_files=root_files,
        readme_content=readme_content,
        gitignore_content=gitignore_content,
        last_commit_date=last_commit_date,
        open_issue_count=open_issue_count,
        now=now,
    )


def scan_account(
    client: GitHubClient,
    owner: str | None = None,
    include_forks: bool = False,
    include_archived: bool = False,
    now: datetime | None = None,
) -> list[RepoHealth]:
    """Scan every repo for `owner` (or the authenticated user if omitted)."""
    repos = client.list_repos(
        owner=owner, include_forks=include_forks, include_archived=include_archived
    )
    return [scan_repo(client, repo, now=now) for repo in repos]
