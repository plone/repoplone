from repoplone import _types as t
from repoplone.utils import _git as gitutils
from repoplone.utils import _github as ghutils
from repoplone.utils import changelog as chgutils
from repoplone.utils import display as dutils
from repoplone.utils import release as utils
from repoplone.utils import versions as vutils

import typer


def check_confirm(
    question: str = "[bold yellow]Continue?[/bold yellow]",
    goodbye: str = "Exiting now",
) -> bool:
    status: bool = dutils.confirm(question)
    if not (status):
        dutils.print(goodbye)
        raise typer.Exit(0)
    return status


def get_next_version(
    settings: t.RepositorySettings, original_version: str, desired_version: str
) -> tuple[str, str]:
    next_version = ""
    error = ""
    try:
        next_version = vutils.next_version(desired_version, original_version)
    except ValueError:
        next_version = ""
        error = "Invalid version."
    else:
        if not utils.valid_next_version(settings, next_version):
            error = f"The version {next_version} already exists as a tag in Git"
            next_version = ""
    return next_version, error


def _step_confirm_version(
    step_id: int,
    title: str,
    settings: t.RepositorySettings,
    original_version: str,
    next_version: str,
    dry_run: bool,
) -> bool:
    dutils.indented_print(f"- Bump version from {settings.version} to {next_version}")
    return check_confirm()


def _step_goodbye(
    step_id: int,
    title: str,
    settings: t.RepositorySettings,
    original_version: str,
    next_version: str,
    dry_run: bool,
) -> bool:
    dutils.indented_print(f"- Completed the release of version {next_version}")
    return check_confirm()


def _step_prepare_changelog(
    step_id: int,
    title: str,
    settings: t.RepositorySettings,
    original_version: str,
    next_version: str,
    dry_run: bool,
) -> bool:
    # Changelog
    ## First display the changelog
    new_entries, _ = chgutils.update_changelog(
        settings, draft=True, version=next_version
    )
    settings._tmp_changelog = new_entries
    text = f"{'=' * 50}\n{new_entries}\n{'=' * 50}"
    dutils.indented_print(text)
    return check_confirm()


def _step_update_repository(
    step_id: int,
    title: str,
    settings: t.RepositorySettings,
    original_version: str,
    next_version: str,
    dry_run: bool,
) -> bool:
    if not dry_run:
        chgutils.update_changelog(settings, draft=dry_run, version=next_version)
        dutils.indented_print(f"- Updated {settings.changelogs.root} file")
    # Update next_version on version.txt
    version_file = settings.version_path
    version_file.write_text(f"{next_version}\n")
    dutils.indented_print(f"- Updated {version_file} file")
    # Update docker-compose.yml
    compose_files = settings.compose_path
    for compose_file in compose_files:
        if compose_file.exists() and compose_file.is_file():
            contents = compose_file.read_text().replace(original_version, next_version)
            compose_file.write_text(contents)
            dutils.indented_print(f"- Updated {compose_file} file")
        else:
            dutils.indented_print(f"- No {compose_file} file to update")
    return True


def _step_release_backend(
    step_id: int,
    title: str,
    settings: t.RepositorySettings,
    original_version: str,
    next_version: str,
    dry_run: bool,
) -> bool:
    if settings.backend.enabled:
        utils.release_backend(settings, next_version, dry_run)
        dutils.indented_print(f"- Released {settings.backend.name}: {next_version}")
    else:
        dutils.indented_print("- Backend packaged is disabled")
    return True


def _step_release_frontend(
    step_id: int,
    title: str,
    settings: t.RepositorySettings,
    original_version: str,
    next_version: str,
    dry_run: bool,
) -> bool:
    if settings.frontend.enabled:
        next_version = vutils.convert_python_node_version(next_version)
        utils.release_frontend(settings, next_version, dry_run)
        dutils.indented_print(f"- Released {settings.frontend.name}: {next_version}")
    else:
        dutils.indented_print("- Frontend packaged is disabled")
    return True


def _step_update_git(
    step_id: int,
    title: str,
    settings: t.RepositorySettings,
    original_version: str,
    next_version: str,
    dry_run: bool,
) -> bool:
    if not dry_run:
        repo = gitutils.repo_for_project(settings.root_path)
        gitutils.finish_release(repo, next_version)
        dutils.indented_print(f"- Created tag {next_version}")
    else:
        dutils.indented_print(f"- Skipped creating tag {next_version}")
    return True


def _step_gh_release(
    step_id: int,
    title: str,
    settings: t.RepositorySettings,
    original_version: str,
    next_version: str,
    dry_run: bool,
) -> bool:
    if dry_run:
        dutils.indented_print("- Skipping GitHub release creation")
        return True
    if ghutils.check_token(settings):
        msg = ghutils.create_release(settings, original_version, next_version)
        dutils.indented_print(msg)
    else:
        dutils.indented_print(
            "- Skipping GitHub release creation as you do not have a GITHUB_TOKEN"
            "environment variable set"
        )
    return True


def get_steps() -> list[t.ReleaseStep]:
    return [
        t.ReleaseStep("version", "Next version", _step_confirm_version),
        t.ReleaseStep("changelog", "Display Changelog", _step_prepare_changelog),
        t.ReleaseStep(
            "update_repository", "Update repository components", _step_update_repository
        ),
        t.ReleaseStep("release_backend", "Release backend", _step_release_backend),
        t.ReleaseStep("release_frontend", "Release frontend", _step_release_frontend),
        t.ReleaseStep("update_git", "Commit changes, create tag", _step_update_git),
        t.ReleaseStep("gh_release", "Create GitHub release", _step_gh_release),
        t.ReleaseStep("", "Goodbye", _step_goodbye),
    ]
