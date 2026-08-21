from unittest.mock import MagicMock, patch

from ghdash.github_client import GitHubClient, get_token


def make_response(status_code=200, json_data=None):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = json_data
    response.raise_for_status.side_effect = (
        None if status_code < 400 else Exception(f"HTTP {status_code}")
    )
    return response


@patch("ghdash.github_client.requests.Session")
def test_list_repos_paginates_and_filters(mock_session_cls):
    session = mock_session_cls.return_value
    page_one = [
        {"full_name": "a/keep", "fork": False, "archived": False},
        {"full_name": "a/fork", "fork": True, "archived": False},
        {"full_name": "a/archived", "fork": False, "archived": True},
    ]
    session.get.side_effect = [make_response(json_data=page_one), make_response(json_data=[])]

    client = GitHubClient(token="fake-token")
    repos = client.list_repos()

    assert [r["full_name"] for r in repos] == ["a/keep"]
    assert session.get.call_count == 2


@patch("ghdash.github_client.requests.Session")
def test_list_repos_include_forks_and_archived(mock_session_cls):
    session = mock_session_cls.return_value
    page_one = [
        {"full_name": "a/keep", "fork": False, "archived": False},
        {"full_name": "a/fork", "fork": True, "archived": False},
        {"full_name": "a/archived", "fork": False, "archived": True},
    ]
    session.get.side_effect = [make_response(json_data=page_one), make_response(json_data=[])]

    client = GitHubClient(token="fake-token")
    repos = client.list_repos(include_forks=True, include_archived=True)

    assert {r["full_name"] for r in repos} == {"a/keep", "a/fork", "a/archived"}


@patch("ghdash.github_client.requests.Session")
def test_list_repos_for_specific_owner_uses_users_endpoint(mock_session_cls):
    session = mock_session_cls.return_value
    session.get.side_effect = [make_response(json_data=[]), make_response(json_data=[])]

    client = GitHubClient(token="fake-token")
    client.list_repos(owner="someone-else")

    called_url = session.get.call_args_list[0].args[0]
    assert called_url == "https://api.github.com/users/someone-else/repos"


@patch("ghdash.github_client.requests.Session")
def test_list_root_contents_returns_files_only(mock_session_cls):
    session = mock_session_cls.return_value
    session.get.return_value = make_response(
        json_data=[{"name": "README.md", "type": "file"}, {"name": "src", "type": "dir"}]
    )

    client = GitHubClient(token="fake-token")
    files = client.list_root_contents("a/repo", "main")

    assert files == ["README.md"]


@patch("ghdash.github_client.requests.Session")
def test_list_root_contents_missing_repo_returns_empty(mock_session_cls):
    session = mock_session_cls.return_value
    session.get.return_value = make_response(status_code=404)

    client = GitHubClient(token="fake-token")
    files = client.list_root_contents("a/empty", "main")

    assert files == []


@patch("ghdash.github_client.requests.Session")
def test_get_file_content_decodes_base64(mock_session_cls):
    import base64

    session = mock_session_cls.return_value
    encoded = base64.b64encode(b"hello world").decode()
    session.get.return_value = make_response(json_data={"encoding": "base64", "content": encoded})

    client = GitHubClient(token="fake-token")
    content = client.get_file_content("a/repo", "README.md", "main")

    assert content == "hello world"


@patch("ghdash.github_client.requests.Session")
def test_get_file_content_missing_file_returns_none(mock_session_cls):
    session = mock_session_cls.return_value
    session.get.return_value = make_response(status_code=404)

    client = GitHubClient(token="fake-token")
    content = client.get_file_content("a/repo", "MISSING.md", "main")

    assert content is None


@patch("ghdash.github_client.requests.Session")
def test_get_latest_commit_date_returns_committer_date(mock_session_cls):
    session = mock_session_cls.return_value
    session.get.return_value = make_response(
        json_data=[{"commit": {"committer": {"date": "2026-08-01T12:00:00Z"}}}]
    )

    client = GitHubClient(token="fake-token")
    date = client.get_latest_commit_date("a/repo", "main")

    assert date == "2026-08-01T12:00:00Z"


@patch("ghdash.github_client.requests.Session")
def test_get_latest_commit_date_empty_repo_returns_none(mock_session_cls):
    session = mock_session_cls.return_value
    session.get.return_value = make_response(status_code=409)

    client = GitHubClient(token="fake-token")
    date = client.get_latest_commit_date("a/empty", "main")

    assert date is None


@patch("ghdash.github_client.requests.Session")
def test_get_latest_commit_date_no_commits_in_body_returns_none(mock_session_cls):
    session = mock_session_cls.return_value
    session.get.return_value = make_response(json_data=[])

    client = GitHubClient(token="fake-token")
    date = client.get_latest_commit_date("a/repo", "main")

    assert date is None


def test_get_open_issue_count_reads_field_from_repo_payload():
    client = GitHubClient.__new__(GitHubClient)  # no session needed for this one
    assert client.get_open_issue_count({"open_issues_count": 5}) == 5
    assert client.get_open_issue_count({}) == 0


@patch.dict("os.environ", {"GITHUB_TOKEN": "env-token"})
def test_get_token_prefers_env_var():
    assert get_token() == "env-token"


@patch.dict("os.environ", {}, clear=True)
@patch("ghdash.github_client.subprocess.run")
def test_get_token_falls_back_to_gh_cli(mock_run):
    mock_run.return_value = MagicMock(returncode=0, stdout="gh-cli-token\n")
    assert get_token() == "gh-cli-token"


@patch.dict("os.environ", {}, clear=True)
@patch("ghdash.github_client.subprocess.run")
def test_get_token_raises_when_nothing_available(mock_run):
    import pytest

    mock_run.return_value = MagicMock(returncode=1, stdout="")
    with pytest.raises(RuntimeError):
        get_token()
