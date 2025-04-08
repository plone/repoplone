from repoplone.utils import release
from repoplone.utils.versions import get_backend_version
from repoplone.utils.versions import get_frontend_version

import pytest


@pytest.fixture
def repo(test_internal_project, initialize_repo):
    repo = initialize_repo(test_internal_project)
    return repo


@pytest.fixture
def settings(repo, bust_path_cache):
    from repoplone.settings import get_settings

    return get_settings()


@pytest.mark.parametrize(
    "version,dry_run,expected",
    [
        ["1.0.0a1", True, "1.0.0a1"],
        ["20250311.1", True, "20250311.1"],
        ["1.0.0a1", False, "1.0.0a1"],
        ["20250311.1", False, "20250311.1"],
    ],
)
def test_release_backend(
    settings, bust_path_cache, version: str, dry_run: bool, expected: str
):
    package = settings.backend
    func = release.release_backend
    func(settings, version, dry_run)
    package_version = get_backend_version(package.path)
    changelog_text = package.changelog.read_text()
    if dry_run:
        assert f"## {expected} (" not in changelog_text
        assert expected != package_version
    else:
        assert f"## {expected} (" in changelog_text
        assert expected == package_version


@pytest.mark.parametrize(
    "version,dry_run,expected",
    [
        ["1.0.0-alpha.1", True, "1.0.0-alpha.1"],
        ["20250311.1", True, "20250311.1.0"],
        ["1.0.0-alpha.1", False, "1.0.0-alpha.1"],
        ["20250311.1", False, "20250311.1.0"],
    ],
)
def test_release_frontend(
    settings, bust_path_cache, version: str, dry_run: bool, expected: str
):
    package = settings.frontend
    func = release.release_frontend
    func(settings, version, dry_run)
    package_version = get_frontend_version(package.path)
    changelog_text = package.changelog.read_text()
    if dry_run:
        assert f"## {expected} (" not in changelog_text
        assert expected != package_version
    else:
        assert f"## {expected} (" in changelog_text
        assert expected == package_version
