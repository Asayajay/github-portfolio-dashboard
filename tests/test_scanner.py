from datetime import datetime, timezone
from unittest.mock import MagicMock

from ghdash.scanner import scan_account, scan_repo

FIXED_NOW = datetime(2026, 8, 20, tzinfo=timezone.utc)

REAL_README = """# My Project

This project does a genuinely useful thing and this sentence exists
purely to push the word count past the stub threshold so the check
actually passes, which is the whole point of writing this test.
"""


def make_client(root_files, readme_content=None, gitignore_content=None, last_commit=None, ):
    client = MagicMock()
    client.list_root_contents.return_value = root_files

    def get_file_content(full_name, path, ref):
        if path.lower().startswith("readme"):
            return readme_content
        if path == ".gitignore":
            return gitignore_content
        return None

    client.get_file_content.side_effect = get_file_content
    client.get_latest_commit_date.return_value = last_commit
    client.get_open_issue_count.return_value = 2
    return client


def test_scan_repo_pulls_root_files_and_scores_health():
    client = make_client(
        root_files=["README.md", "LICENSE", ".gitignore"],
        readme_content=REAL_README,
        gitignore_content="__pycache__/\n.venv/\n.env\ndist/\n",
        last_commit="2026-08-01T00:00:00Z",
    )
    repo = {"full_name": "a/repo", "default_branch": "main"}

    result = scan_repo(client, repo, now=FIXED_NOW)

    assert result.full_name == "a/repo"
    assert result.hygiene_score == 3
    assert result.open_issue_count == 2
    assert result.days_since_last_commit == 19
    client.list_root_contents.assert_called_once_with("a/repo", "main")


def test_scan_repo_skips_file_fetches_when_files_absent():
    client = make_client(root_files=[])
    repo = {"full_name": "a/bare", "default_branch": "main"}

    result = scan_repo(client, repo, now=FIXED_NOW)

    assert result.hygiene_score == 0
    client.get_file_content.assert_not_called()


def test_scan_account_scans_every_listed_repo():
    client = make_client(root_files=["README.md", "LICENSE", ".gitignore"], readme_content=REAL_README)
    client.list_repos.return_value = [
        {"full_name": "a/one", "default_branch": "main"},
        {"full_name": "a/two", "default_branch": "main"},
    ]

    results = scan_account(client, now=FIXED_NOW)

    assert [r.full_name for r in results] == ["a/one", "a/two"]
    client.list_repos.assert_called_once_with(owner=None, include_forks=False, include_archived=False)


def test_scan_account_passes_through_owner_and_flags():
    client = make_client(root_files=[])
    client.list_repos.return_value = []

    scan_account(client, owner="someone-else", include_forks=True, include_archived=True, now=FIXED_NOW)

    client.list_repos.assert_called_once_with(
        owner="someone-else", include_forks=True, include_archived=True
    )
