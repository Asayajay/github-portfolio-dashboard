from ghdash.checks import check_gitignore, check_license, check_readme, find_readme_filename

REAL_README = """# My Project

This project does a genuinely useful thing and this sentence exists
purely to push the word count past the stub threshold so the check
actually passes, which is the whole point of writing this test in
the first place, believe it or not.
"""

FULL_GITIGNORE = """
__pycache__/
*.pyc
.venv/
.env
dist/
build/
"""


def test_check_license_found():
    result = check_license(["README.md", "LICENSE", ".gitignore"])
    assert result.passed
    assert result.issues == []


def test_check_license_missing():
    result = check_license(["README.md", ".gitignore"])
    assert not result.passed
    assert "No LICENSE file found." in result.issues


def test_check_license_case_insensitive_and_alt_names():
    assert check_license(["license.md"]).passed
    assert check_license(["COPYING"]).passed


def test_find_readme_filename_variants():
    assert find_readme_filename(["readme.rst", "LICENSE"]) == "readme.rst"
    assert find_readme_filename(["LICENSE"]) is None


def test_check_readme_missing():
    result = check_readme(["LICENSE"], content=None)
    assert not result.passed
    assert "No README file found." in result.issues


def test_check_readme_empty_file():
    result = check_readme(["README.md"], content="   \n\n  ")
    assert not result.passed
    assert "exists but is empty" in result.issues[0]


def test_check_readme_title_only_stub():
    result = check_readme(["README.md"], content="# My Project\n")
    assert not result.passed
    assert "title-only stub" in result.issues[0]


def test_check_readme_real_content_passes():
    result = check_readme(["README.md"], content=REAL_README)
    assert result.passed
    assert result.issues == []


def test_check_gitignore_missing():
    result = check_gitignore(["README.md"], content=None)
    assert not result.passed
    assert "No .gitignore file found." in result.issues


def test_check_gitignore_empty():
    result = check_gitignore([".gitignore"], content="")
    assert not result.passed
    assert "exists but is empty" in result.issues[0]


def test_check_gitignore_missing_some_categories():
    result = check_gitignore([".gitignore"], content="__pycache__/\n*.pyc\n")
    assert not result.passed
    assert any("virtual environments" in issue for issue in result.issues)
    assert any("environment files" in issue for issue in result.issues)
    assert any("build/output" in issue for issue in result.issues)
    assert not any("Python bytecode" in issue for issue in result.issues)


def test_check_gitignore_full_coverage_passes():
    result = check_gitignore([".gitignore"], content=FULL_GITIGNORE)
    assert result.passed
    assert result.issues == []
