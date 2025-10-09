from datetime import date
from repoplone.cli import app
from typer.testing import CliRunner


runner = CliRunner()


def test_current_version(caplog, test_internal_project_calver, bust_path_cache):
    result = runner.invoke(app, ["versions", "current"])
    assert result.exit_code == 0
    messages = result.stdout.split("\n")
    assert "Current versions" in messages[0]
    assert "Repository" in messages[4]
    assert "fake-project" in messages[4]
    assert "20251006.1" in messages[4]
    assert "Backend" in messages[5]
    assert "fake.project" in messages[5]
    assert "20251006.1" in messages[5]
    assert "Frontend" in messages[6]
    assert "fake-project" in messages[6]
    assert "20251006.1.0" in messages[6]


def test_next_version(caplog, test_internal_project_calver, bust_path_cache):
    result = runner.invoke(app, ["versions", "next"])
    assert result.exit_code == 0
    messages = result.stdout.split("\n")
    assert "Possible next version" in messages[0]
    assert "calver" in messages[4]
    today = date.today().strftime("%Y%m%d")
    assert f"{today}.1" in messages[4]
    assert f"{today}.1.0" in messages[4]
