from repoplone.release import _types as t
from repoplone.utils import changelog as chgutils
from repoplone.utils import display as dutils
from typing import Any


def _update_changelog(settings: t.RepositorySettings, state: t.PipelineState) -> None:
    """Update the root project changelog (skipped on dry-run)."""
    dry_run = state.dry_run
    if not dry_run:
        chgutils.update_changelog(settings, draft=False, version=state.next_version)
    verb = "Would update" if dry_run else "Updated"
    dutils.indented_print(f"- {verb} {settings.changelogs.root} file")


def _update_version_file(
    settings: t.RepositorySettings, state: t.PipelineState
) -> None:
    """Write ``next_version`` to ``settings.version_path`` (skipped on dry-run)."""
    dry_run = state.dry_run
    version_file = settings.version_path
    if not dry_run:
        version_file.write_text(f"{state.next_version}\n")
    verb = "Would update" if dry_run else "Updated"
    dutils.indented_print(f"- {verb} {version_file} file")


def _update_compose_files(
    settings: t.RepositorySettings, state: t.PipelineState
) -> None:
    """Replace ``original_version`` with ``next_version`` in compose files.

    Each compose file in ``settings.compose_path`` is processed independently;
    missing files are reported but never created. Writes are skipped on
    dry-run.
    """
    dry_run = state.dry_run
    verb = "Would update" if dry_run else "Updated"
    for compose_file in settings.compose_path:
        if not (compose_file.exists() and compose_file.is_file()):
            dutils.indented_print(f"- No {compose_file} file to update")
            continue
        if not dry_run:
            contents = compose_file.read_text().replace(
                state.original_version, state.next_version
            )
            compose_file.write_text(contents)
        dutils.indented_print(f"- {verb} {compose_file} file")


def step_update_repository(
    step_id: str,
    title: str,
    settings: t.RepositorySettings,
    state: t.PipelineState,
    **kwargs: Any,
) -> bool:
    """Update repository files for the new version.

    * Project Changelog
    * version.txt
    * docker-compose.yml (if exists)

    On dry-run the files are left untouched; only the planned actions are
    reported.
    """
    _update_changelog(settings, state)
    _update_version_file(settings, state)
    _update_compose_files(settings, state)
    return True
