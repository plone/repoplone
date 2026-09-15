from pathlib import Path
from repoplone import exceptions
from repoplone.cli import app
from typer.testing import CliRunner

import json
import pytest


runner = CliRunner()


DIST_PACKUMENT = {
    "name": "@kitconcept/volto-intranet",
    "versions": {
        "1.0.0-beta.1": {
            "volto_version": "19.0.0",
            "dependencies": {
                "@kitconcept/volto-solr": "^2.0.0",
                "@kitconcept/volto-light-theme": "2.0.0",
            },
        },
    },
}


class _Resp:
    def json(self):
        return DIST_PACKUMENT


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


def test_deps_upgrade_frontend_distribution(
    bust_path_cache,
    monkeypatch,
    test_internal_project_from_distribution,
):
    """Upgrading a distribution-based frontend refreshes distribution.json."""
    from repoplone.commands import dependencies as deps_cmd
    from repoplone.utils.dependencies import distribution as dist_utils
    from repoplone.utils.dependencies import versions as v_utils

    root = test_internal_project_from_distribution
    # Skip the 'make frontend-install' step; avoid the network for the
    # latest-version lookup and the npm packument fetch (but exercise the real
    # sync_distribution logic).
    monkeypatch.setattr(deps_cmd, "_sync_dependencies", lambda *a, **k: None)
    monkeypatch.setattr(
        v_utils, "node_latest_package_version", lambda package: "1.0.0-beta.1"
    )
    monkeypatch.setattr(dist_utils, "get_remote_data", lambda url: _Resp())

    result = runner.invoke(app, ["deps", "upgrade", "frontend", "1.0.0-beta.1"])
    assert result.exit_code == 0, result.stdout

    dist_file = root / "frontend" / "distribution.json"
    assert dist_file.exists()
    data = json.loads(dist_file.read_text())
    assert data["version"] == "1.0.0-beta.1"
    assert data["volto_version"] == "19.0.0"
    assert data["dependencies"]["@kitconcept/volto-solr"] == "^2.0.0"

    mrs = json.loads((root / "frontend" / "mrs.developer.json").read_text())
    assert mrs["core"]["tag"] == "19.0.0"

    package_json = json.loads(
        (root / "frontend" / "packages" / "fake-project" / "package.json").read_text()
    )
    assert package_json["dependencies"]["@kitconcept/volto-intranet"] == "1.0.0-beta.1"


def test_deps_stamp_volto_version(
    bust_path_cache, test_internal_project_from_distribution
):
    root = test_internal_project_from_distribution
    result = runner.invoke(app, ["deps", "stamp-volto-version"])
    assert result.exit_code == 0, result.stdout

    pkg = json.loads(
        (root / "frontend" / "packages" / "fake-project" / "package.json").read_text()
    )
    assert pkg["volto_version"] == "18.14.1"


def test_deps_timeout(
    bust_path_cache, bust_package_versions_cache, requests_timeout, test_public_project
):
    result = runner.invoke(app, ["deps", "check"])
    assert result.exit_code == 1
    exception = result.exception
    assert isinstance(exception, exceptions.RepoPloneExternalException)
    assert "Failed to fetch versions for package" in exception.message
