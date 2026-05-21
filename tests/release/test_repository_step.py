"""Tests for the ``repository`` release step (#29).

The step is split into three helpers, each covered here independently:

* ``_update_changelog`` — delegates to the changelog machinery on a real run
  and is a no-op on dry-run.
* ``_update_version_file`` — writes ``next_version`` to ``settings.version_path``
  on a real run; leaves the file untouched on dry-run.
* ``_update_compose_files`` — replaces ``original_version`` with
  ``next_version`` in compose files; missing files are reported but never
  created; writes are skipped on dry-run.

A single orchestrator test then confirms ``step_update_repository`` wires the
helpers together and reports success.
"""

from repoplone import settings as settings_module
from repoplone.release import _types as t
from repoplone.release.steps import repository as repo_step

import pytest


@pytest.fixture
def captured_output(monkeypatch):
    """Capture indented_print calls from the repository step module."""
    captured: list[str] = []
    monkeypatch.setattr(
        "repoplone.release.steps.repository.dutils.indented_print",
        lambda text: captured.append(text),
    )
    return captured


@pytest.fixture
def stub_changelog(monkeypatch):
    """Replace the changelog updater with a recording stub."""
    calls: list[tuple] = []

    def _stub(settings, draft, version):
        calls.append((settings, draft, version))

    monkeypatch.setattr(
        "repoplone.release.steps.repository.chgutils.update_changelog",
        _stub,
    )
    return calls


@pytest.fixture
def repo_settings(test_public_project, bust_path_cache):
    return settings_module.get_settings()


# ---------------------------------------------------------------------------
# _update_version_file
# ---------------------------------------------------------------------------


def test_update_version_file_dry_run_does_not_write(repo_settings, captured_output):
    version_file = repo_settings.version_path
    original = version_file.read_text()
    state = t.PipelineState(dry_run=True, next_version="9.9.9")

    repo_step._update_version_file(repo_settings, state)

    assert version_file.read_text() == original
    assert captured_output == [f"- Would update {version_file} file"]


def test_update_version_file_real_run_writes(repo_settings, captured_output):
    version_file = repo_settings.version_path
    state = t.PipelineState(dry_run=False, next_version="9.9.9")

    repo_step._update_version_file(repo_settings, state)

    assert version_file.read_text() == "9.9.9\n"
    assert captured_output == [f"- Updated {version_file} file"]


# ---------------------------------------------------------------------------
# _update_compose_files
# ---------------------------------------------------------------------------


def test_update_compose_files_dry_run_does_not_write(repo_settings, captured_output):
    compose_files = [
        path for path in repo_settings.compose_path if path.exists() and path.is_file()
    ]
    assert compose_files, "fixture must contain at least one docker-compose file"
    snapshots = {path: path.read_text() for path in compose_files}
    state = t.PipelineState(
        dry_run=True, original_version="1.0.0", next_version="9.9.9"
    )

    repo_step._update_compose_files(repo_settings, state)

    for path, content in snapshots.items():
        assert path.read_text() == content
    assert any("Would update" in line for line in captured_output)


def test_update_compose_files_real_run_replaces_version(
    repo_settings, captured_output, tmp_path
):
    compose = tmp_path / "docker-compose.yml"
    compose.write_text("image: example:1.0.0\n")
    repo_settings.compose_path = [compose]
    state = t.PipelineState(
        dry_run=False, original_version="1.0.0", next_version="9.9.9"
    )

    repo_step._update_compose_files(repo_settings, state)

    assert compose.read_text() == "image: example:9.9.9\n"
    assert captured_output == [f"- Updated {compose} file"]


def test_update_compose_files_missing_file_reports_no_op(
    repo_settings, captured_output, tmp_path
):
    missing = tmp_path / "absent.yml"
    repo_settings.compose_path = [missing]
    state = t.PipelineState(
        dry_run=False, original_version="1.0.0", next_version="9.9.9"
    )

    repo_step._update_compose_files(repo_settings, state)

    assert not missing.exists()
    assert captured_output == [f"- No {missing} file to update"]


# ---------------------------------------------------------------------------
# _update_changelog
# ---------------------------------------------------------------------------


def test_update_changelog_dry_run_skips_machinery(
    repo_settings, captured_output, stub_changelog
):
    state = t.PipelineState(dry_run=True, next_version="9.9.9")

    repo_step._update_changelog(repo_settings, state)

    assert stub_changelog == []
    assert captured_output == [f"- Would update {repo_settings.changelogs.root} file"]


def test_update_changelog_real_run_invokes_machinery(
    repo_settings, captured_output, stub_changelog
):
    state = t.PipelineState(dry_run=False, next_version="9.9.9")

    repo_step._update_changelog(repo_settings, state)

    assert len(stub_changelog) == 1
    _, draft, version = stub_changelog[0]
    assert draft is False
    assert version == "9.9.9"
    assert captured_output == [f"- Updated {repo_settings.changelogs.root} file"]


# ---------------------------------------------------------------------------
# step_update_repository orchestrator
# ---------------------------------------------------------------------------


def test_step_update_repository_wires_all_helpers(
    repo_settings, captured_output, stub_changelog
):
    """Smoke test: dry-run path returns True and never writes version.txt."""
    version_file = repo_settings.version_path
    original = version_file.read_text()
    state = t.PipelineState(
        dry_run=True, original_version=original.strip(), next_version="9.9.9"
    )

    ok = repo_step.step_update_repository("repository", "Update", repo_settings, state)

    assert ok is True
    assert version_file.read_text() == original
    assert stub_changelog == []
    # One message per artefact: changelog + version.txt + one compose file
    assert len(captured_output) >= 3
    assert all("Would update" in line or "No " in line for line in captured_output)
