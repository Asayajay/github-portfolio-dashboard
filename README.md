# github-portfolio-dashboard

A live health check across every repo in a GitHub account: does it have a
LICENSE, a real README (not just a title), and a .gitignore that covers the
usual junk, plus when it was last touched and how many issues are open. Every
run hits the GitHub API fresh. Nothing here is a saved snapshot.

I built this as the natural next step after
[repo-hygiene-bot](https://github.com/Asayajay/repo-hygiene-bot), which runs
the same three checks and prints a report on demand. This account's project
vault (a personal Obsidian notes folder, not part of this repo) documents
every repo's status by hand, once, at a point in time. This dashboard is the
same underlying checks, but always current, in a browser tab you can refresh
instead of a note you have to remember to update.

## Try it

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pip install -r webapp/requirements.txt   # only needed for the web UI
```

You'll need a GitHub token. If the `gh` CLI is installed and logged in
(`gh auth login`), `ghdash` reads `gh auth token` automatically. Otherwise
set `GITHUB_TOKEN` or `GH_TOKEN` in your environment.

### Command line

```bash
python -m ghdash.cli
```

Scans every repo owned by the authenticated account (forks and archived
repos skipped by default), prints a summary to the terminal, and writes a
timestamped markdown report to `reports/`.

```bash
python -m ghdash.cli --user octocat          # scan someone else's public repos
python -m ghdash.cli --include-forks         # include forked repos
python -m ghdash.cli --include-archived      # include archived repos
python -m ghdash.cli --output-dir docs/reports
python -m ghdash.cli --no-report-file        # print only, skip the file
```

### Web UI

```bash
python webapp/app.py
```

Opens a dashboard at `http://127.0.0.1:8078`: a "Scan now" button, stat tiles
(repos scanned, fully healthy count, average hygiene, total open issues), a
health chart sorted worst to best, and a full table. Every scan is a live
call to `/api/scan`, which runs the same `ghdash` scan the CLI does.

## What "healthy" means here

Three checks, each worth one point out of three:

- **LICENSE** — any of the usual filenames (LICENSE, LICENSE.md, LICENSE.txt,
  LICENCE, COPYING) present at the repo root.
- **README** — present, and with at least 30 words of real body content
  after stripping headings and horizontal rules. A title-only stub doesn't
  count.
- **.gitignore** — present, and covering four common junk categories:
  Python bytecode/cache, virtual environments, `.env` files, and
  build/output directories.

Last commit date and open issue count are reported as plain information,
not scored. A finished side project that hasn't been touched in eight months
isn't unhealthy for that reason alone — it only matters alongside missing
hygiene basics, which is what the score actually measures.

One caveat worth knowing: GitHub's `open_issues_count` field counts open
pull requests as well as issues. There's no separate "issues only" count in
the repo list payload without an extra paginated call per repo, so a repo
with a few open PRs and zero real issues will show a nonzero count here.

## Project layout

- `src/ghdash/github_client.py` — talks to the GitHub REST API (listing
  repos, reading file contents, latest commit date).
- `src/ghdash/checks.py` — the three hygiene checks, as plain functions.
- `src/ghdash/health.py` — turns checks plus commit/issue data into a
  per-repo score, and rolls per-repo results up into an account-wide summary.
- `src/ghdash/scanner.py` — ties the client and the checks together into a
  per-repo result.
- `src/ghdash/report.py` — CLI and markdown report rendering.
- `src/ghdash/cli.py` — the command-line entry point.
- `webapp/` — the Flask app: `app.py` (backend), `templates/`, `static/`.
- `tests/` — one test file per module, plus `test_cli.py` and
  `test_webapp.py`. Every test mocks the GitHub API (`unittest.mock`), so
  the suite runs with no network connection and without touching a real
  account.

## Tests

```bash
pytest
```

## What this doesn't do

- No PR review, contributor activity, or CI status — just the three hygiene
  checks plus commit recency and issue count.
- No caching or scheduling built in. Every scan is a fresh set of GitHub API
  calls (one `list_repos` call, plus a handful of calls per repo). For an
  account with dozens of repos, that's several seconds of live requests
  per scan, which is a deliberate tradeoff for "always current" over "fast."
- No pagination handling for issues/PRs beyond what the repo list payload
  already includes, per the `open_issues_count` caveat above.
