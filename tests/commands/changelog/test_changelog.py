from datetime import datetime
from repoplone.cli import app
from typer.testing import CliRunner


runner = CliRunner()


def test_changelog(test_public_project):
    result = runner.invoke(app, ["changelog"])
    assert result.exit_code == 0
    messages = result.stdout.split("\n")
    now = datetime.now()
    assert f"## 1.0.0a0 ({now:%Y-%m-%d})" in messages
    assert "### Backend" in messages
    assert "- Initial implementation @plone " in messages
