"""Checks on the workflow files that protect the privacy promise (no YAML parser needed)."""
import re
from pathlib import Path

import build

WORKFLOWS = Path(build.ROOT) / ".github" / "workflows"


def workflow(name):
    return (WORKFLOWS / name).read_text(encoding="utf-8")


def test_pages_builds_the_neutral_page_only():
    text = workflow("pages.yml")
    commands = re.findall(r"^\s*run:\s*(.+)$", text, re.M)
    builds = [c for c in commands if "build.py" in c]
    assert builds == ["python build.py --out site/index.html"]
    assert "--demo" not in text and "--profile" not in text


def test_pages_publishes_only_the_built_page():
    text = workflow("pages.yml")
    assert re.search(r"upload-pages-artifact@\S+\s+with:\s+path: site\n", text)
    assert "path: ." not in text


def test_pages_only_runs_after_a_successful_ci_push_on_main():
    text = workflow("pages.yml")
    assert "workflow_run.conclusion == 'success'" in text
    assert "workflow_run.event == 'push'" in text
    assert "pull_request" not in text


def test_pages_has_least_privilege_permissions():
    text = workflow("pages.yml")
    assert re.search(r"^permissions: \{\}$", text, re.M)          # nothing by default
    assert text.count("pages: write") == 1 and text.count("id-token: write") == 1
    assert "packages: write" not in text and "contents: write" not in text


def test_workflows_do_not_log_in_with_personal_tokens():
    for path in WORKFLOWS.glob("*.yml"):
        assert "secrets." not in path.read_text(encoding="utf-8"), path.name
