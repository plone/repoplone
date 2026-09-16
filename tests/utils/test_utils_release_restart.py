"""Cover restarting a release after some packages already reached a registry.

``--start-step release_python`` re-runs the whole step, and a step covers every
package of its family. A package already on PyPI or npm must be skipped rather
than uploaded again.
"""

from repoplone import _types as t
from repoplone.exceptions import RepoPloneExternalException
from repoplone.utils import release as release_utils

import pytest


@pytest.fixture
def multi_settings(test_multi_package_project, bust_path_cache):
    from repoplone import settings as settings_utils

    return settings_utils.get_settings()


@pytest.fixture
def registry(monkeypatch):
    """Stand in for PyPI and npm, recording what was asked for."""
    published: dict[str, list[str]] = {}
    asked: list[str] = []

    def lookup(package_name: str = "") -> list[str]:
        asked.append(package_name)
        return published.get(package_name, [])

    monkeypatch.setattr(release_utils.dep_versions, "pypi_package_versions", lookup)
    monkeypatch.setattr(release_utils.dep_versions, "npm_package_versions", lookup)
    return published, asked


def test_already_published_checks_pypi_for_python_packages(multi_settings, registry):
    published, asked = registry
    package = multi_settings.packages_for(t.FAMILY_PYTHON)[0]
    published[package.name] = ["1.0.0"]
    assert release_utils.already_published(package, "1.0.0") is True
    assert asked == [package.name]


def test_already_published_is_false_for_a_new_version(multi_settings, registry):
    published, _ = registry
    package = multi_settings.packages_for(t.FAMILY_PYTHON)[0]
    published[package.name] = ["0.9.0"]
    assert release_utils.already_published(package, "1.0.0") is False


def test_already_published_checks_npm_for_node_packages(multi_settings, registry):
    published, _ = registry
    package = multi_settings.packages_for(t.FAMILY_NODE)[0]
    published[package.name] = ["1.0.0"]
    assert release_utils.already_published(package, "1.0.0") is True


def test_an_unreachable_registry_does_not_skip(multi_settings, monkeypatch):
    """Publishing and being rejected beats silently skipping a package.

    A network failure must not read as "already published": that would leave
    a package unreleased while the run reports success.
    """

    def boom(package_name: str = "") -> list[str]:
        raise RepoPloneExternalException("no network")

    monkeypatch.setattr(release_utils.dep_versions, "pypi_package_versions", boom)
    package = multi_settings.packages_for(t.FAMILY_PYTHON)[0]
    assert release_utils.already_published(package, "1.0.0") is False


def test_restart_skips_the_package_already_on_pypi(
    multi_settings, registry, monkeypatch
):
    published, _ = registry
    package = multi_settings.packages_for(t.FAMILY_PYTHON)[0]
    published[package.name] = ["1.0.0"]

    built: list[str] = []
    monkeypatch.setattr(release_utils.PoCompile, "run", lambda self: None)
    monkeypatch.setattr(release_utils, "update_backend_changelog", lambda *a, **k: "")
    monkeypatch.setattr(release_utils, "UV", lambda path: _NoopUV())
    monkeypatch.setattr(
        release_utils,
        "update_backend_version",
        lambda path, version: built.append(str(path)),
    )
    release_utils.release_backend(multi_settings, package, "1.0.0", dry_run=False)
    assert built == []


def test_restart_still_releases_the_package_that_did_not_publish(
    multi_settings, registry, monkeypatch
):
    """The point of the check: the rest of the family still gets released."""
    published, _ = registry
    first, second = multi_settings.packages_for(t.FAMILY_PYTHON)
    published[first.name] = ["1.0.0"]

    released: list[str] = []
    monkeypatch.setattr(
        release_utils,
        "update_backend_version",
        lambda path, version: released.append(str(path)),
    )
    monkeypatch.setattr(release_utils, "update_backend_changelog", lambda *a, **k: "")
    monkeypatch.setattr(release_utils.PoCompile, "run", lambda self: None)

    class _UV:
        def __init__(self, path):
            pass

        def build(self):
            pass

        def publish(self):
            pass

    monkeypatch.setattr(release_utils, "UV", _UV)

    release_utils.release_backend(multi_settings, first, "1.0.0", dry_run=False)
    release_utils.release_backend(multi_settings, second, "1.0.0", dry_run=False)
    assert released == [str(second.path)]


def test_a_dry_run_never_asks_the_registry(multi_settings, registry, monkeypatch):
    """Nothing is uploaded on a dry run, so nothing needs checking."""
    _, asked = registry
    package = multi_settings.packages_for(t.FAMILY_PYTHON)[0]
    monkeypatch.setattr(release_utils.PoCompile, "run", lambda self: None)
    monkeypatch.setattr(release_utils, "UV", lambda path: _NoopUV())
    release_utils.release_backend(multi_settings, package, "1.0.0", dry_run=True)
    assert asked == []


class _NoopUV:
    def build(self):
        pass

    def publish(self):
        pass


def test_a_package_that_does_not_publish_is_never_checked(
    multi_settings, registry, monkeypatch
):
    _, asked = registry
    package = multi_settings.packages_for(t.FAMILY_PYTHON)[0]
    package.publish = False
    monkeypatch.setattr(release_utils.PoCompile, "run", lambda self: None)
    monkeypatch.setattr(release_utils, "update_backend_version", lambda *a: None)
    monkeypatch.setattr(release_utils, "update_backend_changelog", lambda *a, **k: "")
    monkeypatch.setattr(release_utils, "UV", lambda path: _NoopUV())
    release_utils.release_backend(multi_settings, package, "1.0.0", dry_run=False)
    assert asked == []
