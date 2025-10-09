from repoplone import _types as t
from repoplone.utils import settings as utils

import pytest


@pytest.fixture
def get_settings():
    def func() -> t.RepositorySettings:
        from repoplone import settings

        return settings.get_settings()

    return func


def test_internal_project_settings(
    bust_path_cache, test_internal_project, get_settings
):
    settings = get_settings()
    func = utils.settings_to_dict
    result = func(settings)
    assert isinstance(result, dict)
    assert result["name"] == "fake-project"
    assert result["container_images_prefix"] == "ghcr.io/organization/fake-project"
    assert result["version_format"] == "semver"


def test_internal_project_calver_settings(
    bust_path_cache, test_internal_project_calver, get_settings
):
    settings = get_settings()
    func = utils.settings_to_dict
    result = func(settings)
    assert isinstance(result, dict)
    assert result["name"] == "fake-project"
    assert result["container_images_prefix"] == ""
    assert result["version_format"] == "calver"


def test_internal_project_from_distribution_settings(
    bust_path_cache, test_internal_project_from_distribution, get_settings
):
    settings = get_settings()
    func = utils.settings_to_dict
    result = func(settings)
    assert isinstance(result, dict)
    assert result["name"] == "fake-project"
    assert result["container_images_prefix"] == "ghcr.io/organization/fake-project"
    assert result["version_format"] == "calver"


def test_addon_settings(bust_path_cache, test_addon, get_settings):
    settings = get_settings()
    func = utils.settings_to_dict
    result = func(settings)
    assert isinstance(result, dict)
    assert result["name"] == "fake-addon"
    assert result["container_images_prefix"] == "ghcr.io/organization/fake-addon"
    assert result["version_format"] == "semver"
    assert result["backend"]["base_package_version"] == "6.1.0"
