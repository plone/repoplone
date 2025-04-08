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
        ["backend", t.Package],
        ["frontend", t.Package],
        ["version_path", Path],
        ["compose_path", Path],
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
    assert isinstance(backend, t.Package)
    assert backend.publish is True
    frontend = result.frontend
    assert isinstance(frontend, t.Package)
    assert frontend.publish is True


def test_internal_project_packages(test_internal_project, bust_path_cache):
    result = settings.get_settings()
    backend = result.backend
    assert isinstance(backend, t.Package)
    assert backend.publish is False
    assert backend.base_package == "Products.CMFPlone"
    frontend = result.frontend
    assert isinstance(frontend, t.Package)
    assert frontend.publish is False
    assert frontend.base_package == "@plone/volto"
