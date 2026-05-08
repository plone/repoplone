from pathlib import Path
from repoplone.cli import app
from typer.testing import CliRunner

import json
import pytest
import shutil
import sys


runner = CliRunner()


@pytest.fixture(autouse=True)
def _restore_sys_state():
    original_path = list(sys.path)
    original_modules = set(sys.modules)
    yield
    sys.path[:] = original_path
    for mod_name in list(sys.modules):
        if mod_name not in original_modules:
            del sys.modules[mod_name]


@pytest.fixture
def project(test_resources_dir, monkeypatch, tmp_path) -> Path:
    src = test_resources_dir / "fake-project-from-distribution"
    dst = tmp_path / "fake-project-from-distribution"
    shutil.copytree(src, dst)
    monkeypatch.chdir(dst)
    return dst


@pytest.fixture
def project_with_release_section(project) -> Path:
    toml = project / "repository.toml"
    toml.write_text(
        toml.read_text()
        + "\n[repository.release]\n"
        + 'steps = ["changelog", "notify_slack", "bye"]\n\n'
        + "[repository.release.registry.notify_slack]\n"
        + 'title = "Notify Slack"\n'
        + 'function = "local_step"\n'
        + 'args = { entrypoint = "scripts.notify:hook" }\n'
    )
    return project


def _write_hook(project: Path):
    scripts = project / "scripts"
    scripts.mkdir(exist_ok=True)
    (scripts / "__init__.py").write_text("")
    (scripts / "notify.py").write_text(
        "def hook(step_id, title, settings, state, **kwargs):\n    return True\n"
    )


def test_sanity_check_default_pipeline(bust_path_cache, project):
    result = runner.invoke(app, ["settings", "sanity-check"])
    assert result.exit_code == 0
    assert "Settings OK" in result.stdout


def test_sanity_check_with_resolvable_local_step(
    bust_path_cache, project_with_release_section
):
    _write_hook(project_with_release_section)
    result = runner.invoke(app, ["settings", "sanity-check"])
    assert result.exit_code == 0
    assert "Settings OK" in result.stdout


def test_sanity_check_fails_when_local_step_module_missing(
    bust_path_cache, project_with_release_section
):
    result = runner.invoke(app, ["settings", "sanity-check"])
    assert result.exit_code == 1
    assert "notify_slack" in result.stdout
    assert "ImportError" in result.stdout or "ModuleNotFoundError" in result.stdout


def test_release_steps_table_default(bust_path_cache, project):
    result = runner.invoke(app, ["settings", "release-steps"])
    assert result.exit_code == 0
    assert "Release pipeline steps" in result.stdout
    assert "changelog" in result.stdout
    assert "built-in" in result.stdout


def test_release_steps_json_default(bust_path_cache, project):
    result = runner.invoke(app, ["settings", "release-steps", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert isinstance(data, list)
    ids = [row["id"] for row in data]
    assert ids == [
        "changelog",
        "version",
        "repository",
        "release_backend",
        "release_frontend",
        "git",
        "gh_release",
        "bye",
    ]
    assert all(row["source"] == "built-in" for row in data)


def test_release_steps_json_with_registered_alias(
    bust_path_cache, project_with_release_section
):
    _write_hook(project_with_release_section)
    result = runner.invoke(app, ["settings", "release-steps", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    notify = next(row for row in data if row["id"] == "notify_slack")
    assert notify["function"] == "local_step"
    assert notify["source"] == "registered"
    assert notify["title"] == "Notify Slack"
