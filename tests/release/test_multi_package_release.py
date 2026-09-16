"""Cover the release pipeline and changelog for repositories with many packages.

The release steps loop over a family; the component-level work stays on its
primary package.
"""

from repoplone import _types as t
from repoplone import settings as settings_utils
from repoplone.release import pipeline
from repoplone.release.steps import node as node_step
from repoplone.release.steps import python as python_step
from repoplone.utils import changelog as changelog_utils
from repoplone.utils import release as release_utils

import pytest


@pytest.fixture
def multi_settings(test_multi_package_project, bust_path_cache):
    return settings_utils.get_settings()


@pytest.fixture
def root_settings(test_root_package_project, bust_path_cache):
    return settings_utils.get_settings()


@pytest.fixture
def spec1_settings(test_public_project, bust_path_cache):
    """A spec 1 monorepo, loaded with the cwd cache busted.

    The shared ``settings`` fixture does not bust it, so it can answer with
    whichever project a previous test in the module chdir-ed into.
    """
    return settings_utils.get_settings()


@pytest.fixture
def state():
    return t.PipelineState(dry_run=True, next_version="1.0.0")


# --- Steps loop over their family ----------------------------------------


def test_release_python_step_covers_every_package(
    multi_settings, state, monkeypatch, capsys
):
    released: list[str] = []
    monkeypatch.setattr(
        python_step.utils,
        "release_backend",
        lambda settings, package, version, dry_run: released.append(package.name),
    )
    assert python_step.step_release_python("id", "t", multi_settings, state) is True
    assert released == ["acme.core", "acme.theme"]


def test_release_node_step_covers_every_package(
    multi_settings, state, monkeypatch, capsys
):
    released: list[str] = []
    monkeypatch.setattr(
        node_step.utils,
        "release_frontend",
        lambda settings, package, version, dry_run: released.append(package.name),
    )
    assert node_step.step_release_node("id", "t", multi_settings, state) is True
    assert released == ["@acme/volto-core", "@acme/volto-theme"]


def test_release_steps_run_at_each_package_path(multi_settings, state, monkeypatch):
    """Each package is released at its own path, not the primary's."""
    paths: list[str] = []
    monkeypatch.setattr(
        python_step.utils,
        "release_backend",
        lambda settings, package, version, dry_run: paths.append(package.path.name),
    )
    python_step.step_release_python("id", "t", multi_settings, state)
    assert paths == ["backend", "acme.theme"]


def test_release_step_is_skipped_for_an_empty_family(
    root_settings, state, monkeypatch, capsys
):
    released: list[str] = []
    monkeypatch.setattr(
        node_step.utils,
        "release_frontend",
        lambda settings, package, version, dry_run: released.append(package.name),
    )
    assert node_step.step_release_node("id", "t", root_settings, state) is True
    assert released == []
    assert "No Node package" in capsys.readouterr().out


def test_process_steps_drops_the_step_of_an_empty_family(root_settings):
    ids = [step.id for step in pipeline.process_steps(root_settings)]
    assert "release_python" in ids
    assert "release_node" not in ids


# --- Towncrier sections ---------------------------------------------------


def test_one_section_per_package(multi_settings):
    ids = [section.section_id for section in multi_settings.towncrier.sections]
    assert ids == [
        "python",
        "python:acme.theme",
        "node",
        "node:@acme/volto-theme",
        "repository",
    ]


def test_spec2_section_titles_are_package_names(multi_settings):
    names = [section.name for section in multi_settings.towncrier.sections]
    assert names == [
        "acme.core",
        "acme.theme",
        "@acme/volto-core",
        "@acme/volto-theme",
        "Project",
    ]


def test_spec1_section_titles_are_unchanged(spec1_settings):
    """Upgrading repoplone must not rewrite an existing project's headings."""
    names = [section.name for section in spec1_settings.towncrier.sections]
    assert names == ["Backend", "Frontend"]


def test_spec1_section_ids_follow_the_families(spec1_settings):
    ids = [section.section_id for section in spec1_settings.towncrier.sections]
    assert ids == ["python", "node"]


def test_legacy_section_attributes_still_resolve(multi_settings):
    """Project hooks read settings.towncrier.backend; that must keep working."""
    assert multi_settings.towncrier.backend.section_id == "python"
    assert multi_settings.towncrier.frontend.section_id == "node"


def test_section_get_reaches_non_primary_packages(multi_settings):
    section = multi_settings.towncrier.get("python:acme.theme")
    assert section is not None
    assert section.name == "acme.theme"


def test_section_get_returns_none_for_unknown(multi_settings):
    assert multi_settings.towncrier.get("python:nope") is None


def test_missing_section_attribute_still_raises(multi_settings):
    with pytest.raises(AttributeError):
        _ = multi_settings.towncrier.nope


# --- Changelog ------------------------------------------------------------


def test_changelog_draft_has_one_section_per_package(multi_settings):
    entry, _ = changelog_utils.update_changelog(
        multi_settings, draft=True, version="1.0.0"
    )
    for name in ("acme.core", "acme.theme", "@acme/volto-core", "@acme/volto-theme"):
        assert f"### {name}" in entry


def test_changelog_reports_each_package_own_changes(multi_settings):
    entry, _ = changelog_utils.update_changelog(
        multi_settings, draft=True, version="1.0.0"
    )
    assert "Added the first thing" in entry
    assert "Added the theme thing" in entry
    assert "Added the core block" in entry
    assert "Added the theme block" in entry


def test_frontend_changelog_copy_is_primary_only(multi_settings):
    """With several node packages the last one would otherwise win."""
    frontend_changelog = multi_settings.root_path / "frontend" / "CHANGELOG.md"
    frontend_changelog.write_text("# Untouched\n")
    secondary = multi_settings.packages_for(t.FAMILY_NODE)[1]
    changelog_utils.update_frontend_changelog(
        multi_settings, secondary, draft=False, version="1.0.0"
    )
    assert frontend_changelog.read_text() == "# Untouched\n"


def test_frontend_changelog_copy_runs_for_the_primary(multi_settings):
    frontend_changelog = multi_settings.root_path / "frontend" / "CHANGELOG.md"
    frontend_changelog.write_text("# Untouched\n")
    primary = multi_settings.packages_for(t.FAMILY_NODE)[0]
    changelog_utils.update_frontend_changelog(
        multi_settings, primary, draft=False, version="1.0.0"
    )
    assert frontend_changelog.read_text() != "# Untouched\n"


def test_root_level_package_changelog_is_written_once(root_settings):
    """A package at the repository root owns the repository changelog.

    Its own towncrier build writes that file, so the aggregated entry must
    leave it alone -- otherwise every change is reported twice, under two
    different headings.
    """
    package = root_settings.packages[0]
    assert package.changelog == root_settings.changelogs.root

    changelog_utils.update_changelog(root_settings, draft=False, version="1.0.0")
    changelog_utils.update_backend_changelog(
        root_settings, package, draft=False, version="1.0.0"
    )

    text = root_settings.changelogs.root.read_text()
    assert text.count("Added the root thing") == 1


def test_root_level_package_still_previews_its_changes(root_settings):
    """Skipping the aggregated write must not empty the preview."""
    entry, _ = changelog_utils.update_changelog(
        root_settings, draft=True, version="1.0.0"
    )
    assert "Added the root thing" in entry


# --- Authentication -------------------------------------------------------


def test_authentication_is_checked_once_per_family(multi_settings, monkeypatch):
    uv_calls: list[str] = []
    npm_calls: list[str] = []

    class _UV:
        def __init__(self, path):
            uv_calls.append(str(path))

        def check_authentication(self):
            return True

    class _ReleaseIt:
        def __init__(self, path):
            npm_calls.append(str(path))

        def check_authentication(self):
            return True

    monkeypatch.setattr(release_utils, "UV", _UV)
    monkeypatch.setattr(release_utils, "ReleaseIt", _ReleaseIt)
    monkeypatch.setattr(release_utils, "gh_check_token", lambda settings: "token")

    result = release_utils.sanity_check(multi_settings)
    assert result.errors == []
    assert len(uv_calls) == 1
    assert len(npm_calls) == 1
