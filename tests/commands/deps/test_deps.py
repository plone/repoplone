from pathlib import Path
from repoplone import exceptions
from repoplone.cli import app
from typer.testing import CliRunner

import pytest


runner = CliRunner()


@pytest.mark.vcr
def test_deps_info(
    bust_path_cache,
    in_project_path: Path,
    in_package_name: str,
    idx: int,
    title: str,
    package_name: str,
):
    result = runner.invoke(app, ["deps", "info"])
    assert result.exit_code == 0
    messages = result.stdout.splitlines()
    assert "Base packages" in messages[0]
    assert title in messages[idx]
    assert package_name in messages[idx]


@pytest.mark.vcr
def test_deps_check(
    caplog,
    bust_path_cache,
    in_project_path,
    in_package_name,
    idx: int,
    component: str,
    package_name: str,
    current_version: str,
    latest_version: str,
):
    result = runner.invoke(app, ["deps", "check"])
    assert result.exit_code == 0
    messages = result.stdout.splitlines()
    assert "Base packages versions" in messages[0]
    assert component in messages[idx]
    assert package_name in messages[idx]
    assert current_version in messages[idx]
    assert latest_version in messages[idx]


@pytest.mark.vcr
def test_deps_upgrade(
    bust_path_cache,
    in_project_path,
    in_package_name,
    in_patch_sync,
    component,
    package_name,
    version,
    expected,
):
    result = runner.invoke(app, ["deps", "upgrade", component, version])
    assert result.exit_code == 0
    messages = result.stdout.splitlines()
    assert expected in messages


def test_deps_timeout(
    bust_path_cache, bust_package_versions_cache, requests_timeout, test_public_project
):
    result = runner.invoke(app, ["deps", "check"])
    assert result.exit_code == 1
    exception = result.exception
    assert isinstance(exception, exceptions.RepoPloneExternalException)
    assert "Failed to fetch versions for package" in exception.message
