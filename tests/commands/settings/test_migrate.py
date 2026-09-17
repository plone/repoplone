"""Cover ``repoplone settings migrate``.

The command rewrites a spec 1 ``repository.toml`` into spec 2 through tomlkit,
so the comments and formatting of a file people read survive the migration.
"""

from pathlib import Path
from repoplone.cli import app
from repoplone.settings import migrate
from typer.testing import CliRunner

import json
import pytest
import tomlkit


runner = CliRunner()


COMMENTED_SPEC1 = """# The repository this project releases.
[repository]
name = "fake-project"
changelog = "CHANGELOG.md"
version = "version.txt"
# A single compose file, written the deprecated way.
compose = "docker-compose.yml"
managed_by_uv = true

[backend]
path = "backend"

[backend.package]
name = "fake.project"  # the distribution package
path = "backend"
changelog = "backend/CHANGELOG.md"
towncrier_settings = "backend/pyproject.toml"
publish = false

[frontend]
path = "frontend"

[frontend.package]
name = "fake-project"
path = "frontend/packages/fake-project"
changelog = "frontend/packages/fake-project/CHANGELOG.md"
towncrier_settings = "frontend/packages/fake-project/towncrier.toml"
publish = false

# cookieplone wrote this and repoplone never reads it.
[cookieplone]
template = "monorepo_addon"
"""


@pytest.fixture
def spec1_file(tmp_path) -> Path:
    path = tmp_path / "repository.toml"
    path.write_text(COMMENTED_SPEC1)
    return path


@pytest.fixture
def migrated(spec1_file) -> str:
    text, _ = migrate.migrate_file(spec1_file)
    return text


@pytest.fixture
def migrated_data(migrated) -> dict:
    return tomlkit.parse(migrated).unwrap()


def test_spec_version_comes_first(migrated: str):
    assert migrated.startswith('spec_version = "2"')


def test_component_tables_are_gone(migrated_data: dict):
    assert "backend" not in migrated_data
    assert "frontend" not in migrated_data


def test_packages_become_an_array(migrated_data: dict):
    assert [entry["type"] for entry in migrated_data["package"]] == [
        "python-plone",
        "node-volto",
    ]
    assert [entry["name"] for entry in migrated_data["package"]] == [
        "fake.project",
        "fake-project",
    ]


def test_each_family_gets_one_primary(migrated_data: dict):
    assert all(entry["primary"] for entry in migrated_data["package"])


def test_deprecated_keys_are_dropped(migrated_data: dict):
    assert "managed_by_uv" not in migrated_data["repository"]


def test_compose_becomes_a_list(migrated_data: dict):
    assert migrated_data["repository"]["compose"] == ["docker-compose.yml"]


def test_unknown_tables_are_left_alone(migrated_data: dict):
    """cookieplone's table is none of repoplone's business."""
    assert migrated_data["cookieplone"]["template"] == "monorepo_addon"


def test_comments_survive(migrated: str):
    assert "# The repository this project releases." in migrated
    assert "# A single compose file, written the deprecated way." in migrated
    assert "# the distribution package" in migrated


def test_a_comment_trailing_a_removed_table_is_reported(spec1_file):
    """TOML nests such a comment inside the table being removed.

    tomlkit cannot place an unkeyed item at a chosen position, and appending
    it would put the comment below whatever it introduced. Reporting it lets
    the author put it back where they meant it.
    """
    _, notes = migrate.migrate_file(spec1_file)
    joined = "\n".join(notes)
    assert "Dropped a comment that followed [frontend]" in joined
    assert "# cookieplone wrote this" in joined


def test_result_matches_the_spec2_schema(migrated: str):
    migrate.validate_migrated(migrated)


def test_notes_report_every_change(spec1_file):
    _, notes = migrate.migrate_file(spec1_file)
    joined = "\n".join(notes)
    assert "managed_by_uv" in joined
    assert "compose" in joined
    assert "python-plone" in joined


def test_notes_report_the_changelog_heading_change(spec1_file):
    """Migrating is when section titles become package names, so say so."""
    _, notes = migrate.migrate_file(spec1_file)
    joined = "\n".join(notes)
    assert "Changelog sections" in joined
    assert 'section = "Backend"' in joined


def test_no_section_keys_are_written(migrated_data: dict):
    """Preserving the old headings would pin spec 1 behaviour into the file."""
    assert all("section" not in entry for entry in migrated_data["package"])


def test_release_steps_are_renamed(tmp_path):
    path = tmp_path / "repository.toml"
    path.write_text(
        '[repository]\nname = "x"\n\n'
        "[repository.release]\n"
        'steps = ["changelog", "release_backend", "release_frontend", "bye"]\n\n'
        "[repository.release.registry.extra]\n"
        'function = "release_backend"\n'
    )
    text, notes = migrate.migrate_file(path)
    data = tomlkit.parse(text).unwrap()
    assert data["repository"]["release"]["steps"] == [
        "changelog",
        "release_python",
        "release_node",
        "bye",
    ]
    assert data["repository"]["release"]["registry"]["extra"]["function"] == (
        "release_python"
    )
    assert any("release_backend -> release_python" in note for note in notes)


def test_a_spec2_file_is_refused(tmp_path):
    path = tmp_path / "repository.toml"
    path.write_text('spec_version = "2"\n\n[repository]\nname = "x"\n')
    with pytest.raises(migrate.MigrationError, match="already declares"):
        migrate.migrate_file(path)


def test_a_missing_file_is_refused(tmp_path):
    with pytest.raises(migrate.MigrationError, match=r"No repository\.toml"):
        migrate.migrate_file(tmp_path / "nope.toml")


# --- Through the CLI ------------------------------------------------------


def test_cli_migrate(test_public_project, bust_path_cache):
    result = runner.invoke(app, ["settings", "migrate"])
    assert result.exit_code == 0
    assert "specification 2" in result.stdout
    text = (test_public_project / "repository.toml").read_text()
    assert text.startswith('spec_version = "2"')
    assert "[[package]]" in text

    # The migrated file is what repoplone reads next.
    from repoplone import settings as settings_utils

    settings_utils.get_cwd_path.cache_clear()
    result = settings_utils.get_settings()
    assert result.spec_version == 2
    assert [package.name for package in result.packages] == [
        "fake.distribution",
        "fake-distribution",
    ]


def test_cli_migrate_dry_run_writes_nothing(test_public_project, bust_path_cache):
    original = (test_public_project / "repository.toml").read_text()
    result = runner.invoke(app, ["settings", "migrate", "--dry-run"])
    assert result.exit_code == 0
    assert "was not modified" in result.stdout
    assert (test_public_project / "repository.toml").read_text() == original


def test_cli_migrate_dry_run_prints_the_table_headers(
    test_public_project, bust_path_cache
):
    """Rich would read [[package]] as markup and swallow it."""
    result = runner.invoke(app, ["settings", "migrate", "--dry-run"])
    assert "[[package]]" in result.stdout
    assert "[repository]" in result.stdout


def test_cli_migrate_refuses_a_spec2_project(
    test_multi_package_project, bust_path_cache
):
    result = runner.invoke(app, ["settings", "migrate"])
    assert result.exit_code != 0


def test_cli_dump_reports_the_new_keys(test_multi_package_project, bust_path_cache):
    result = runner.invoke(app, ["settings", "dump"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["spec_version"] == 2
    assert [package["name"] for package in data["packages"]] == [
        "acme.core",
        "acme.theme",
        "@acme/volto-core",
        "@acme/volto-theme",
    ]
    # The spec 1 keys are still there, holding each family's primary package.
    assert data["backend"]["name"] == "acme.core"
    assert data["frontend"]["name"] == "@acme/volto-core"
