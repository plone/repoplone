from repoplone.cli import app
from typer.testing import CliRunner

import logging
import pytest


runner = CliRunner()


@pytest.mark.vcr
def test_deps_info(
    caplog,
    bust_path_cache,
    in_pyproject_toml,
    in_package_name: str,
    expected: str,
):
    result = runner.invoke(app, ["deps", "info"])
    assert result.exit_code == 0
    with caplog.at_level(logging.INFO):
        messages = [record.message for record in caplog.records]
    assert f"The base package is {expected}" in messages


@pytest.mark.vcr
def test_deps_check(
    caplog,
    bust_path_cache,
    in_pyproject_toml,
    in_package_name: str,
    update_pyproject,
    current_version: str,
    in_latest_version: str,
):
    update_pyproject(in_pyproject_toml, in_package_name, current_version, [])
    result = runner.invoke(app, ["deps", "check"])
    assert result.exit_code == 0
    with caplog.at_level(logging.INFO):
        messages = [record.message for record in caplog.records]
    assert (
        f"Current version {current_version}, latest version {in_latest_version}"
        in messages
    )


@pytest.mark.vcr
def test_deps_upgrade(
    bust_path_cache, in_pyproject_toml, in_package_name, toml_parse, version: str
):
    result = runner.invoke(app, ["deps", "upgrade", version])
    assert result.exit_code == 0
    data = toml_parse(in_pyproject_toml)
    assert f"{in_package_name}=={version}" in data["project"]["dependencies"]
    tool_uv = data["tool"]["uv"]
    assert "constraint-dependencies" in tool_uv
    assert f"{in_package_name}=={version}" in tool_uv["constraint-dependencies"]
