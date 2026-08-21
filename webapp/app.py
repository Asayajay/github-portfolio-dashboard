"""Flask backend for the live dashboard.

Every request to /api/scan hits the GitHub API fresh -- there's no cached
snapshot sitting behind this, which is the whole point versus the vault's
manually-compiled notes. The GitHubClient itself is cheap to construct
(it just resolves a token), so a new one per request is fine.
"""

import os
import sys
from dataclasses import asdict

from flask import Flask, jsonify, render_template, request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from ghdash.github_client import GitHubClient
from ghdash.health import summarize_portfolio
from ghdash.scanner import scan_account

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/scan")
def api_scan():
    owner = request.args.get("owner") or None
    include_forks = request.args.get("include_forks") == "true"
    include_archived = request.args.get("include_archived") == "true"

    try:
        client = GitHubClient()
        results = scan_account(
            client, owner=owner, include_forks=include_forks, include_archived=include_archived
        )
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 500

    summary = summarize_portfolio(results)

    return jsonify(
        {
            "summary": asdict(summary),
            "repos": [asdict(r) for r in sorted(results, key=lambda r: r.hygiene_percent)],
        }
    )


if __name__ == "__main__":
    app.run(debug=True, port=8078)
