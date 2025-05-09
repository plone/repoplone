from pathlib import Path
from repoplone.cli import app
from typer.testing import CliRunner

import json
import pytest
import shutil


runner = CliRunner()


@pytest.fixture
def project(test_resources_dir, monkeypatch, tmp_path) -> Path:
    src = test_resources_dir / "fake-project-from-distribution"
    dst = tmp_path / "fake-project-from-distribution"
    shutil.copytree(src, dst)
    monkeypatch.chdir(dst)
    return dst


@pytest.fixture
def dump_result(project):
    result = runner.invoke(app, ["settings", "dump"])
    assert result.exit_code == 0
    output = result.stdout
    return json.loads(output)


def test_settings_dump(bust_path_cache, project):
    result = runner.invoke(app, ["settings", "dump"])
    assert result.exit_code == 0
    output = result.stdout
    data = json.loads(output)
    assert isinstance(data, dict)
    assert isinstance(data["backend"], dict)
    assert isinstance(data["frontend"], dict)
    assert isinstance(data["version"], str)


@pytest.mark.parametrize(
    "path,expected",
    [
        [("version",), "1.0.0a0"],
        [("backend", "base_package"), "kitconcept.intranet"],
        [("backend", "base_package_version"), "1.0.0a17"],
        [("backend", "version"), "1.0.0a0"],
        [("frontend", "base_package"), "@kitconcept/intranet"],
        [("frontend", "base_package_version"), "1.0.0-alpha.17"],
        [("frontend", "volto_version"), "18.14.1"],
        [("frontend", "version"), "1.0.0-alpha.0"],
    ],
)
def test_settings_dump_values(dump_result, path: tuple[str, ...], expected):
    value = dump_result
    for key in path:
        value = value.get(key)
    assert value == expected
