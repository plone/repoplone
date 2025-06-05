from datetime import datetime
from repoplone.cli import app
from typer.testing import CliRunner

import pytest


runner = CliRunner()


def test_changelog(test_public_project):
    result = runner.invoke(app, ["changelog"])
    assert result.exit_code == 0
    messages = result.stdout.split("\n")
    now = datetime.now()
    assert f"## 1.0.0a0 ({now:%Y-%m-%d})" in messages
    assert "### Backend" in messages
    assert "- Initial implementation @plone " in messages


@pytest.mark.parametrize("subdir", ["backend", "frontend"])
def test_changelog_in_subcommand(test_public_project, monkeypatch, subdir: str):
    # Change the current working directory to the subdirectory
    cwd = test_public_project / subdir
    monkeypatch.chdir(cwd)
    # Run the changelog command
    result = runner.invoke(app, ["changelog"])
    assert result.exit_code == 0
    messages = result.stdout.split("\n")
    now = datetime.now()
    assert f"## 1.0.0a0 ({now:%Y-%m-%d})" in messages
    assert "### Backend" in messages
    assert "- Initial implementation @plone " in messages
