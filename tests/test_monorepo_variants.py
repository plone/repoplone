from repoplone import settings
from repoplone.cli import app
from repoplone.release.pipeline import ReleasePipeline
from repoplone.utils import changelog as changelog_utils
from typer.testing import CliRunner

import pytest


@pytest.fixture
def runner():
    return CliRunner()


def test_backend_only_settings(test_backend_only_project, bust_path_cache):
    result = settings.get_settings()
    assert result.backend.enabled is True
    assert result.frontend.enabled is False
    assert result.sanity() is True

    # Check changelog fallback
    assert result.changelogs.frontend == result.changelogs.root
    assert result.changelogs.backend != result.changelogs.root


def test_frontend_only_settings(test_frontend_only_project, bust_path_cache):
    result = settings.get_settings()
    assert result.backend.enabled is False
    assert result.frontend.enabled is True
    assert result.sanity() is True

    # Check changelog fallback
    assert result.changelogs.backend == result.changelogs.root
    assert result.changelogs.frontend != result.changelogs.root


def test_backend_only_versions_next(test_backend_only_project, bust_path_cache, runner):
    result = runner.invoke(app, ["versions", "next"])
    assert result.exit_code == 0
    assert "Backend" in result.stdout
    assert "Frontend" not in result.stdout


def test_frontend_only_versions_next(
    test_frontend_only_project, bust_path_cache, runner
):
    result = runner.invoke(app, ["versions", "next"])
    assert result.exit_code == 0
    assert "Frontend" in result.stdout
    assert "Backend" not in result.stdout


def test_backend_only_deps_info(test_backend_only_project, bust_path_cache, runner):
    result = runner.invoke(app, ["deps", "info"])
    assert result.exit_code == 0
    assert "Backend" in result.stdout
    assert "Frontend" not in result.stdout


def test_frontend_only_deps_info(test_frontend_only_project, bust_path_cache, runner):
    result = runner.invoke(app, ["deps", "info"])
    assert result.exit_code == 0
    assert "Frontend" in result.stdout
    assert "Backend" not in result.stdout


def test_backend_only_pipeline_steps(test_backend_only_project, bust_path_cache):
    res_settings = settings.get_settings()
    pipeline = ReleasePipeline(res_settings)
    step_ids = [s.id for s in pipeline.steps]
    assert "release_backend" in step_ids
    assert "release_frontend" not in step_ids


def test_frontend_only_pipeline_steps(test_frontend_only_project, bust_path_cache):
    res_settings = settings.get_settings()
    pipeline = ReleasePipeline(res_settings)
    step_ids = [s.id for s in pipeline.steps]
    assert "release_frontend" in step_ids
    assert "release_backend" not in step_ids


def test_backend_only_changelog_utils(test_backend_only_project, bust_path_cache):
    res_settings = settings.get_settings()
    assert changelog_utils.update_frontend_changelog(res_settings) == ""


def test_frontend_only_changelog_utils(test_frontend_only_project, bust_path_cache):
    res_settings = settings.get_settings()
    assert changelog_utils.update_backend_changelog(res_settings) == ""


def test_backend_only_deps_upgrade_frontend_error(
    test_backend_only_project, bust_path_cache, runner
):
    result = runner.invoke(app, ["deps", "upgrade", "frontend", "1.0.0"])
    assert result.exit_code == 1
    assert "Error: Frontend component is not enabled" in result.stdout


def test_frontend_only_deps_upgrade_backend_error(
    test_frontend_only_project, bust_path_cache, runner
):
    result = runner.invoke(app, ["deps", "upgrade", "backend", "1.0.0"])
    assert result.exit_code == 1
    assert "Error: Backend component is not enabled" in result.stdout


@pytest.mark.parametrize("component", ["FRONTEND", "Frontend", "FrOnTeNd"])
def test_deps_upgrade_component_case_insensitive(
    test_backend_only_project, bust_path_cache, runner, component
):
    """Mixed-case component names are normalized before validation.

    Reaching the "not enabled" gate (rather than "must be either") proves the
    value was lowercased: an un-normalized "FRONTEND" would be rejected as an
    invalid component instead.
    """
    result = runner.invoke(app, ["deps", "upgrade", component, "1.0.0"])
    assert result.exit_code == 1
    assert "Error: Frontend component is not enabled" in result.stdout
    assert "Component must be either" not in result.stdout


@pytest.mark.parametrize("component", ["FRONTEND", "Frontend", "FrOnTeNd"])
def test_deps_sync_component_case_insensitive(
    test_backend_only_project, bust_path_cache, runner, component
):
    """``deps sync`` normalizes the component name before the enabled check."""
    result = runner.invoke(app, ["deps", "sync", component])
    assert result.exit_code == 1
    assert "Error: Frontend component is not enabled" in result.stdout
    assert "Component must be either" not in result.stdout


@pytest.mark.parametrize("component", ["BACKEND", "Backend", "BaCkEnD"])
def test_deps_constraints_component_case_insensitive(
    test_frontend_only_project, bust_path_cache, runner, component
):
    """``deps constraints`` accepts mixed-case ``backend`` past validation.

    On a frontend-only project it stops at the uv-managed guard instead of the
    invalid-component error, confirming the name was normalized.
    """
    result = runner.invoke(app, ["deps", "constraints", component])
    assert result.exit_code == 0
    assert "Component must be 'backend'." not in result.stdout


@pytest.mark.parametrize("component", ["back", "end", "acken", "backendX"])
def test_deps_constraints_rejects_substrings(
    test_backend_only_project, bust_path_cache, runner, component
):
    """Substrings of "backend" must be rejected, not accepted.

    Guards against the regression where ``component not in ("backend")`` did a
    substring membership test, wrongly accepting e.g. "back" or "end".
    """
    result = runner.invoke(app, ["deps", "constraints", component])
    assert result.exit_code == 1
    assert "Component must be 'backend'." in result.stdout


def test_backend_only_no_section_settings(
    test_backend_only_no_section_project, bust_path_cache
):
    result = settings.get_settings()
    assert result.backend.enabled is True
    assert result.frontend.enabled is False
    assert result.sanity() is True

    # Check changelog fallback
    assert result.changelogs.frontend == result.changelogs.root
    assert result.changelogs.backend != result.changelogs.root


def test_backend_only_no_section_versions_next(
    test_backend_only_no_section_project, bust_path_cache, runner
):
    result = runner.invoke(app, ["versions", "next"])
    assert result.exit_code == 0
    assert "Backend" in result.stdout
    assert "Frontend" not in result.stdout


def test_frontend_only_no_section_settings(
    test_frontend_only_no_section_project, bust_path_cache
):
    result = settings.get_settings()
    assert result.backend.enabled is False
    assert result.frontend.enabled is True
    assert result.sanity() is True

    # Check changelog fallback
    assert result.changelogs.backend == result.changelogs.root
    assert result.changelogs.frontend != result.changelogs.root


def test_frontend_only_no_section_versions_next(
    test_frontend_only_no_section_project, bust_path_cache, runner
):
    result = runner.invoke(app, ["versions", "next"])
    assert result.exit_code == 0
    assert "Frontend" in result.stdout
    assert "Backend" not in result.stdout
