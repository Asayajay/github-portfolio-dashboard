from unittest.mock import patch

from ghdash.cli import main


def make_scan_results():
    from datetime import datetime, timezone

    from ghdash.health import compute_repo_health

    return [
        compute_repo_health(
            full_name="a/repo",
            root_files=["README.md", "LICENSE", ".gitignore"],
            readme_content="# Repo\n\n" + "word " * 40,
            gitignore_content="__pycache__/\n.venv/\n.env\ndist/\n",
            last_commit_date="2026-08-19T00:00:00Z",
            open_issue_count=1,
            now=datetime(2026, 8, 20, tzinfo=timezone.utc),
        )
    ]


@patch("ghdash.cli.write_markdown_report")
@patch("ghdash.cli.scan_account")
@patch("ghdash.cli.GitHubClient")
def test_main_prints_report_and_writes_file(mock_client_cls, mock_scan, mock_write, capsys, tmp_path):
    mock_scan.return_value = make_scan_results()
    mock_write.return_value = tmp_path / "portfolio-report-fake.md"

    exit_code = main([])

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "a/repo" in out
    assert "Wrote" in out
    mock_write.assert_called_once()


@patch("ghdash.cli.scan_account")
@patch("ghdash.cli.GitHubClient")
def test_main_no_report_file_skips_writing(mock_client_cls, mock_scan, capsys):
    mock_scan.return_value = make_scan_results()

    exit_code = main(["--no-report-file"])

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "Wrote" not in out


@patch("ghdash.cli.scan_account")
@patch("ghdash.cli.GitHubClient")
def test_main_passes_user_and_flags_through(mock_client_cls, mock_scan):
    mock_scan.return_value = []

    main(["--user", "someone-else", "--include-forks", "--include-archived", "--no-report-file"])

    _, kwargs = mock_scan.call_args
    assert kwargs["owner"] == "someone-else"
    assert kwargs["include_forks"] is True
    assert kwargs["include_archived"] is True


@patch("ghdash.cli.GitHubClient")
def test_main_reports_missing_token_as_clean_error(mock_client_cls, capsys):
    mock_client_cls.side_effect = RuntimeError("No GitHub token found.")

    exit_code = main([])

    err = capsys.readouterr().err
    assert exit_code == 1
    assert "No GitHub token found." in err
