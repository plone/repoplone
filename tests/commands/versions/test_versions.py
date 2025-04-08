from repoplone.cli import app
from typer.testing import CliRunner


runner = CliRunner()


def test_current_version(caplog, test_public_project):
    result = runner.invoke(app, ["versions", "current"])
    assert result.exit_code == 0
    messages = result.stdout.split("\n")
    assert "Current versions" in messages[0]
    assert "Repository" in messages[4]
    assert "fake-distribution" in messages[4]
    assert "1.0.0a0" in messages[4]
    assert "Backend" in messages[5]
    assert "fake.distribution" in messages[5]
    assert "1.0.0a0" in messages[5]
    assert "Frontend" in messages[6]
    assert "fake-distribution" in messages[6]
    assert "1.0.0-alpha.0" in messages[6]


def test_next_version(caplog, test_public_project):
    result = runner.invoke(app, ["versions", "next"])
    assert result.exit_code == 0
    messages = result.stdout.split("\n")
    assert "Possible next version" in messages[0]
    assert "release" in messages[5]
    assert "major" in messages[6]
