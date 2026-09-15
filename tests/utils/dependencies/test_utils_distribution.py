from repoplone.utils.dependencies import distribution as dist_utils
from repoplone.utils.dependencies import frontend as frontend_utils

import json
import pytest


PACKUMENT = {
    "name": "@kitconcept/volto-intranet",
    "versions": {
        "1.0.0-alpha.17": {
            "volto_version": "18.14.1",
            "dependencies": {
                "@kitconcept/volto-solr": "^1.0.0-alpha.4",
                "@kitconcept/volto-light-theme": "1.0.0-alpha.10",
            },
        },
        "1.0.0-beta.1": {
            "volto_version": "19.0.0",
            "dependencies": {
                "@kitconcept/volto-solr": "^2.0.0",
                "@kitconcept/volto-light-theme": "2.0.0",
            },
        },
        "1.0.0-beta.2": {
            # No volto_version published for this release.
            "dependencies": {"@kitconcept/volto-solr": "^2.0.1"},
        },
    },
}


class Resp:
    def __init__(self, data):
        self._data = data

    def json(self):
        return self._data


@pytest.fixture
def mock_npm(monkeypatch):
    monkeypatch.setattr(dist_utils, "get_remote_data", lambda url: Resp(PACKUMENT))


@pytest.fixture
def dist_settings(bust_path_cache, test_internal_project_from_distribution):
    """Settings for the distribution project."""
    from repoplone import settings

    return settings.get_settings()


def test_fetch_distribution_metadata(mock_npm):
    deps, volto_version = dist_utils.fetch_distribution_metadata(
        "@kitconcept/volto-intranet", "1.0.0-beta.1"
    )
    assert volto_version == "19.0.0"
    assert deps["@kitconcept/volto-solr"] == "^2.0.0"


def test_fetch_distribution_metadata_no_volto_version(mock_npm):
    deps, volto_version = dist_utils.fetch_distribution_metadata(
        "@kitconcept/volto-intranet", "1.0.0-beta.2"
    )
    assert volto_version is None
    assert deps == {"@kitconcept/volto-solr": "^2.0.1"}


def test_fetch_distribution_metadata_unknown_version(mock_npm):
    with pytest.raises(ValueError):
        dist_utils.fetch_distribution_metadata("@kitconcept/volto-intranet", "9.9.9")


def test_sync_distribution_writes_file(dist_settings, mock_npm):
    frontend_root = dist_settings.frontend.path.parent.parent
    dist_file = frontend_root / dist_utils.DISTRIBUTION_FILENAME
    assert not dist_file.exists()

    assert dist_utils.sync_distribution(dist_settings, "1.0.0-beta.1") is True

    data = json.loads(dist_file.read_text())
    assert data["name"] == "@kitconcept/volto-intranet"
    assert data["version"] == "1.0.0-beta.1"
    assert data["volto_version"] == "19.0.0"
    assert data["dependencies"]["@kitconcept/volto-solr"] == "^2.0.0"


def test_sync_distribution_updates_core_tag(dist_settings, mock_npm):
    frontend_root = dist_settings.frontend.path.parent.parent
    mrs_path = frontend_root / "mrs.developer.json"

    dist_utils.sync_distribution(dist_settings, "1.0.0-beta.1")

    data = json.loads(mrs_path.read_text())
    assert data["core"]["tag"] == "19.0.0"


def test_sync_distribution_skips_without_volto_version(dist_settings, mock_npm):
    """A base package without volto_version is not treated as a distribution."""
    frontend_root = dist_settings.frontend.path.parent.parent
    mrs_path = frontend_root / "mrs.developer.json"
    original_tag = json.loads(mrs_path.read_text())["core"]["tag"]
    dist_file = frontend_root / dist_utils.DISTRIBUTION_FILENAME

    assert dist_utils.sync_distribution(dist_settings, "1.0.0-beta.2") is False

    # Neither distribution.json nor the core tag are touched.
    assert not dist_file.exists()
    data = json.loads(mrs_path.read_text())
    assert data["core"]["tag"] == original_tag


def test_stamp_volto_version(dist_settings):
    version = dist_utils.stamp_volto_version(dist_settings)
    # mrs.developer core.tag of the distribution fixture project.
    assert version == "18.14.1"
    pkg = json.loads((dist_settings.frontend.path / "package.json").read_text())
    assert pkg["volto_version"] == "18.14.1"


def test_stamp_volto_version_missing_tag(dist_settings):
    frontend_root = dist_settings.frontend.path.parent.parent
    mrs_path = frontend_root / "mrs.developer.json"
    data = json.loads(mrs_path.read_text())
    del data["core"]["tag"]
    mrs_path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        dist_utils.stamp_volto_version(dist_settings)


def test_update_core_tag_no_volto_entry(tmp_path):
    mrs_path = tmp_path / "mrs.developer.json"
    mrs_path.write_text(json.dumps({"other": {"package": "@acme/thing"}}))
    changed = frontend_utils.update_core_tag_mrs_developer(tmp_path, "19.0.0")
    assert changed is False
