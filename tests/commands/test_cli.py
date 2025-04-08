from repoplone import __version__
from repoplone.cli import app
from typer.testing import CliRunner


runner = CliRunner()


def test_cli_option_version(test_public_project, bust_path_cache):
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert f"repoplone {__version__}" in result.stdout
