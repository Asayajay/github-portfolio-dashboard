import os
import sys
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

WEBAPP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "webapp")
sys.path.insert(0, WEBAPP_DIR)

from app import app  # noqa: E402

from ghdash.health import compute_repo_health  # noqa: E402


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def fake_results():
    now = datetime(2026, 8, 20, tzinfo=timezone.utc)
    return [
        compute_repo_health(
            full_name="a/healthy",
            root_files=["README.md", "LICENSE", ".gitignore"],
            readme_content="# Repo\n\n" + "word " * 40,
            gitignore_content="__pycache__/\n.venv/\n.env\ndist/\n",
            last_commit_date="2026-08-19T00:00:00Z",
            open_issue_count=0,
            now=now,
        ),
        compute_repo_health(
            full_name="a/bare",
            root_files=[],
            readme_content=None,
            gitignore_content=None,
            last_commit_date=None,
            open_issue_count=3,
            now=now,
        ),
    ]


def test_index_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200


@patch("app.scan_account")
@patch("app.GitHubClient")
def test_scan_endpoint_returns_summary_and_sorted_repos(mock_client_cls, mock_scan, client):
    mock_scan.return_value = fake_results()

    response = client.get("/api/scan")

    assert response.status_code == 200
    body = response.get_json()
    assert body["summary"]["repo_count"] == 2
    # Sorted ascending by hygiene_percent, so the bare repo comes first.
    assert body["repos"][0]["full_name"] == "a/bare"
    assert body["repos"][1]["full_name"] == "a/healthy"


@patch("app.scan_account")
@patch("app.GitHubClient")
def test_scan_endpoint_passes_query_params_through(mock_client_cls, mock_scan, client):
    mock_scan.return_value = []

    client.get("/api/scan?owner=someone-else&include_forks=true&include_archived=true")

    _, kwargs = mock_scan.call_args
    assert kwargs["owner"] == "someone-else"
    assert kwargs["include_forks"] is True
    assert kwargs["include_archived"] is True


@patch("app.GitHubClient")
def test_scan_endpoint_reports_missing_token_as_clean_error(mock_client_cls, client):
    mock_client_cls.side_effect = RuntimeError("No GitHub token found.")

    response = client.get("/api/scan")

    assert response.status_code == 500
    assert "error" in response.get_json()
