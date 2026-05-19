from repoplone import _types as t
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
