"""Hygiene checks: LICENSE, README completeness, .gitignore coverage.

Same thresholds as repo-hygiene-bot's checks (same author, same account) --
these ran against every repo in this account already, so there's no reason
to invent different rules for the same three checks here.
"""

from __future__ import annotations

from dataclasses import dataclass, field

LICENSE_FILENAMES = {"license", "license.md", "license.txt", "licence", "copying"}
MIN_README_BODY_WORDS = 30

GITIGNORE_CATEGORIES = {
    "Python bytecode/cache (__pycache__, *.pyc)": ["pycache", ".pyc", ".pyo"],
    "virtual environments (.venv/venv)": [".venv", "venv", "virtualenv"],
    "environment files (.env)": [".env"],
    "build/output directories (dist, build, node_modules, etc.)": [
        "dist",
        "build",
        "egg-info",
        "node_modules",
        ".next",
        "target/",
        "out/",
    ],
}


@dataclass
class CheckResult:
    passed: bool
    issues: list[str] = field(default_factory=list)


def check_license(root_files: list[str]) -> CheckResult:
    found = any(name.lower() in LICENSE_FILENAMES for name in root_files)
    if found:
        return CheckResult(passed=True)
    return CheckResult(passed=False, issues=["No LICENSE file found."])


def find_readme_filename(root_files: list[str]) -> str | None:
    for name in root_files:
        if name.lower().startswith("readme"):
            return name
    return None


def _readme_body_text(content: str) -> str:
    body_lines = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        if set(stripped) <= {"-"} or set(stripped) <= {"="}:
            continue
        body_lines.append(stripped)
    return " ".join(body_lines)


def check_readme(root_files: list[str], content: str | None) -> CheckResult:
    filename = find_readme_filename(root_files)
    if filename is None:
        return CheckResult(passed=False, issues=["No README file found."])

    if content is None or not content.strip():
        return CheckResult(passed=False, issues=[f"{filename} exists but is empty."])

    word_count = len(_readme_body_text(content).split())
    if word_count < MIN_README_BODY_WORDS:
        return CheckResult(
            passed=False,
            issues=[
                f"{filename} looks like a title-only stub "
                f"({word_count} words of body content, need at least {MIN_README_BODY_WORDS})."
            ],
        )
    return CheckResult(passed=True)


def check_gitignore(root_files: list[str], content: str | None) -> CheckResult:
    if not any(name.lower() == ".gitignore" for name in root_files):
        return CheckResult(passed=False, issues=["No .gitignore file found."])

    if content is None or not content.strip():
        return CheckResult(passed=False, issues=[".gitignore exists but is empty."])

    lines = [
        line.strip().lstrip("!").lower()
        for line in content.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    missing_categories = [
        label
        for label, keywords in GITIGNORE_CATEGORIES.items()
        if not any(keyword in line for line in lines for keyword in keywords)
    ]

    if missing_categories:
        return CheckResult(
            passed=False,
            issues=[f".gitignore doesn't cover {label}." for label in missing_categories],
        )
    return CheckResult(passed=True)
