from repoplone.release import _types as t
from repoplone.utils import changelog as chgutils
from repoplone.utils import display as dutils


def step_update_repository(
    step_id: str, title: str, settings: t.RepositorySettings, state: t.PipelineState
) -> bool:
    """Update repository files for the new version.

    * Project Changelog
    * version.txt
    * docker-compose.yml (if exists)
    """
    if not state.dry_run:
        # Update changelog
        chgutils.update_changelog(
            settings, draft=state.dry_run, version=state.next_version
        )
        dutils.indented_print(f"- Updated {settings.changelogs.root} file")
    # Update next_version on version.txt
    version_file = settings.version_path
    version_file.write_text(f"{state.next_version}\n")
    dutils.indented_print(f"- Updated {version_file} file")
    # Update docker-compose.yml
    compose_files = settings.compose_path
    for compose_file in compose_files:
        if compose_file.exists() and compose_file.is_file():
            contents = compose_file.read_text().replace(
                state.original_version, state.next_version
            )
            compose_file.write_text(contents)
            dutils.indented_print(f"- Updated {compose_file} file")
        else:
            dutils.indented_print(f"- No {compose_file} file to update")
    return True
