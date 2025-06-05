from pathlib import Path
from repoplone import _types as t
from repoplone import settings

import pytest


@pytest.mark.parametrize(
    "attr,expected",
    [
        ["name", str],
        ["root_path", Path],
        ["version", str],
        ["backend", t.BackendPackage],
        ["frontend", t.FrontendPackage],
        ["version_path", Path],
        ["compose_path", list],
        ["towncrier", t.TowncrierSettings],
        ["changelogs", t.Changelogs],
    ],
)
def test_get_settings(test_public_project, bust_path_cache, attr: str, expected):
    result = settings.get_settings()
    assert isinstance(result, t.RepositorySettings)
    settings_atts = getattr(result, attr)
    assert isinstance(settings_atts, expected)


def test_settings_sanity(test_public_project, bust_path_cache):
    result = settings.get_settings()
    assert isinstance(result, t.RepositorySettings)
    assert result.sanity() is True


def test_public_project_packages(test_public_project, bust_path_cache):
    result = settings.get_settings()
    backend = result.backend
    assert isinstance(backend, t.BackendPackage)
    assert backend.publish is True
    frontend = result.frontend
    assert isinstance(frontend, t.FrontendPackage)
    assert frontend.publish is True


def test_internal_project_base_packages(
    test_internal_project_from_distribution, bust_path_cache
):
    result = settings.get_settings()
    backend = result.backend
    assert isinstance(backend, t.BackendPackage)
    assert backend.base_package == "kitconcept.intranet"
    assert backend.base_package_version == "1.0.0a17"
    frontend = result.frontend
    assert isinstance(frontend, t.FrontendPackage)
    assert frontend.base_package == "@kitconcept/intranet"
    assert frontend.base_package_version == "1.0.0-alpha.17"
    assert frontend.volto_version == "18.14.1"


def test_internal_project_packages(test_internal_project, bust_path_cache):
    result = settings.get_settings()
    backend = result.backend
    assert isinstance(backend, t.BackendPackage)
    assert backend.publish is False
    assert backend.managed_by_uv is True
    assert backend.base_package == "Products.CMFPlone"
    frontend = result.frontend
    assert isinstance(frontend, t.FrontendPackage)
    assert frontend.publish is False
    assert frontend.base_package == "@plone/volto"


@pytest.mark.parametrize(
    "path,expected_warnings,message",
    [
        [
            "repository_toml/deprecated_100.toml",
            4,
            (
                "Setting repository.managed_by_uv is deprecated and will be removed"
                " in version 1.0.0"
            ),
        ],
        [
            "repository_toml/deprecated_100.toml",
            4,
            "Setting backend.path is deprecated and will be removed in version 1.0.0",
        ],
        [
            "repository_toml/deprecated_100.toml",
            4,
            "Setting frontend.path is deprecated and will be removed in version 1.0.0",
        ],
        [
            "repository_toml/old-compose.toml",
            1,
            (
                "Setting repository.compose as `str` is deprecated and will be "
                "removed in version 1.0.0"
            ),
        ],
        ["repository_toml/updated.toml", 0, ""],
    ],
)
def test_deprecations(
    repository_toml_factory, path: str, expected_warnings: int, message: str
):
    import warnings

    root_path = repository_toml_factory(path)
    func = settings._get_raw_settings
    with warnings.catch_warnings(record=True) as w:
        func(root_path)
    total_warnings = len(w)
    assert total_warnings == expected_warnings
    if total_warnings:
        messages = [str(deprecation.message) for deprecation in w]
        assert message in messages
