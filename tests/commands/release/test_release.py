from repoplone.cli import app
from typer.testing import CliRunner


runner = CliRunner()


def test_release_no_version(bust_path_cache, test_public_project):
    result = runner.invoke(app, ["release"])
    assert result.exit_code == 0
    output = result.stdout
    assert "release [OPTIONS] DESIRED_VERSION COMMAND" in output
    assert "Could be the version" in output
