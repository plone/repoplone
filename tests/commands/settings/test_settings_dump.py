from repoplone.cli import app
from typer.testing import CliRunner

import json


runner = CliRunner()


def test_settings_dump(bust_path_cache, test_public_project):
    result = runner.invoke(app, ["settings", "dump"])
    assert result.exit_code == 0
    output = result.stdout
    data = json.loads(output)
    assert isinstance(data, dict)
    assert isinstance(data["backend"], dict)
    assert isinstance(data["frontend"], dict)
    assert isinstance(data["version"], str)
