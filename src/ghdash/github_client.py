"""Thin wrapper around the GitHub REST API for the data the dashboard needs."""

from __future__ import annotations

import base64
import os
import subprocess

import requests

API_ROOT = "https://api.github.com"


def get_token() -> str:
    """Resolve a GitHub token, preferring the gh CLI's stored credentials."""
    env_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if env_token:
        return env_token

    result = subprocess.run(
        ["gh", "auth", "token"], capture_output=True, text=True, check=False
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()

    raise RuntimeError("No GitHub token found. Run 'gh auth login' or set GITHUB_TOKEN.")


class GitHubClient:
    """Talks to the GitHub REST API: repos, root contents, file contents,
    latest commit, and open issue count."""

    def __init__(self, token: str | None = None):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token or get_token()}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )

    def list_repos(
        self,
        owner: str | None = None,
        include_forks: bool = False,
        include_archived: bool = False,
    ) -> list[dict]:
        """List repos for the authenticated user, or the public repos of `owner`."""
        repos = []
        page = 1
        while True:
            params = {"per_page": 100, "page": page}
            if owner:
                url = f"{API_ROOT}/users/{owner}/repos"
            else:
                url = f"{API_ROOT}/user/repos"
                params["affiliation"] = "owner"

            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            batch = response.json()
            if not batch:
                break

            for repo in batch:
                if repo.get("fork") and not include_forks:
                    continue
                if repo.get("archived") and not include_archived:
                    continue
                repos.append(repo)

            page += 1

        return repos

    def list_root_contents(self, full_name: str, ref: str) -> list[str]:
        """Return filenames present at the repo root (empty repos return [])."""
        url = f"{API_ROOT}/repos/{full_name}/contents/"
        response = self.session.get(url, params={"ref": ref}, timeout=30)
        if response.status_code == 404:
            return []
        response.raise_for_status()
        return [entry["name"] for entry in response.json() if entry["type"] == "file"]

    def get_file_content(self, full_name: str, path: str, ref: str) -> str | None:
        """Fetch and decode a file's text content, or None if it doesn't exist."""
        url = f"{API_ROOT}/repos/{full_name}/contents/{path}"
        response = self.session.get(url, params={"ref": ref}, timeout=30)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        data = response.json()
        if data.get("encoding") != "base64":
            return None
        return base64.b64decode(data["content"]).decode("utf-8", errors="replace")

    def get_latest_commit_date(self, full_name: str, ref: str) -> str | None:
        """Return the ISO commit date of the most recent commit on `ref`, or
        None for a genuinely empty repo (no commits yet)."""
        url = f"{API_ROOT}/repos/{full_name}/commits"
        response = self.session.get(url, params={"sha": ref, "per_page": 1}, timeout=30)
        if response.status_code in (404, 409):
            # 409 Conflict is what GitHub returns for a repo with zero commits.
            return None
        response.raise_for_status()
        commits = response.json()
        if not commits:
            return None
        return commits[0]["commit"]["committer"]["date"]

    def get_open_issue_count(self, repo: dict) -> int:
        """Open issue count straight from the repo object.

        GitHub's `open_issues_count` field counts open pull requests too,
        not just issues -- there's no separate "issues only" count in the
        repo payload without an extra paginated call per repo. Documented
        here rather than hidden, since it can overstate the real issue
        backlog on repos with several open PRs.
        """
        return repo.get("open_issues_count", 0)
