from repoplone.utils import changelog

import pytest


@pytest.mark.parametrize(
    "version",
    [
        "1.0.0a1",
        "1.0.0b1",
        "1.0.0rc1",
        "1.0.0",
    ],
)
def test_update_changelog_draft(settings, version: str):
    func = changelog.update_changelog
    new_entries, fullchangelog = func(settings=settings, draft=True, version=version)
    assert f"## {version} (" in fullchangelog
    assert f"## {version} (" in new_entries
    assert "### Backend" in new_entries
    assert "### Frontend" in new_entries


@pytest.mark.parametrize(
    "version",
    [
        "1.0.0a1",
        "1.0.0b1",
        "1.0.0rc1",
        "1.0.0",
    ],
)
def test_update_changelog(settings, version: str):
    old_project_changelog = settings.changelogs.root.read_text()
    func = changelog.update_changelog
    new_entries, _ = func(settings=settings, draft=False, version=version)
    new_project_changelog = settings.changelogs.root.read_text()
    assert old_project_changelog != new_project_changelog
    assert new_entries in new_project_changelog
    assert f"## {version} (" in new_project_changelog
    assert f"## {version} (" in new_entries
    assert "### Backend" in new_entries
    assert "### Frontend" in new_entries


@pytest.mark.parametrize(
    "version,draft",
    [
        ["1.0.0a1", True],
        ["1.0.0b1", True],
        ["1.0.0rc1", True],
        ["1.0.0", True],
        ["1.0.0a1", False],
        ["1.0.0b1", False],
        ["1.0.0rc1", False],
        ["1.0.0", False],
    ],
)
def test_update_backend_changelog(settings, version: str, draft: bool):
    old_changelog = settings.backend.changelog.read_text()
    func = changelog.update_backend_changelog
    result = func(settings=settings, draft=draft, version=version)
    new_changelog = settings.backend.changelog.read_text()
    if draft:
        assert old_changelog == new_changelog
        assert result not in new_changelog
    else:
        assert old_changelog != new_changelog
        assert "Done" in result


@pytest.mark.parametrize(
    "section_id,total",
    [["backend", 1], ["frontend", 1]],
)
def test__find_fragments(settings, section_id: str, total: int):
    func = changelog._find_fragments
    section = getattr(settings, section_id)
    path = section.path
    towncrier_settings = section.towncrier
    results = func(path, towncrier_settings)
    assert len(results) == total


@pytest.mark.parametrize(
    "section_id,total",
    [
        ["backend", 1],
        ["frontend", 1],
        ["repository", 2],
    ],
)
def test__find_fragments_root(settings_root_changelog, section_id: str, total: int):
    func = changelog._find_fragments
    towncrier_settings = getattr(settings_root_changelog.towncrier, section_id)
    section = getattr(settings_root_changelog, section_id, settings_root_changelog)
    path = section.path
    results = func(path, towncrier_settings.path)
    assert len(results) == total
