from repoplone import _types as t
from repoplone.utils import _git as gitutils
from repoplone.utils import _github as ghutils
from repoplone.utils import changelog as chgutils
from repoplone.utils import display as dutils
from repoplone.utils import release as utils
from repoplone.utils import versions as vutils
from typing import Annotated

import typer


app = typer.Typer()


def _check_for_confirmation(
    question: str = "[bold yellow]Continue?[/bold yellow]",
    goodbye: str = "Exiting now",
) -> bool:
    status: bool = dutils.confirm(question)
    if not (status):
        dutils.print(goodbye)
        raise typer.Exit(0)
    return status


def _get_next_version(
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
    return _check_for_confirmation()


def _step_goodbye(
    step_id: int,
    title: str,
    settings: t.RepositorySettings,
    original_version: str,
    next_version: str,
    dry_run: bool,
) -> bool:
    dutils.indented_print(f"- Completed the release of version {next_version}")
    return _check_for_confirmation()


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
    return _check_for_confirmation()


def _step_update_repository(
    step_id: int,
    title: str,
    settings: t.RepositorySettings,
    original_version: str,
    next_version: str,
    dry_run: bool,
):
    if not dry_run:
        chgutils.update_changelog(settings, draft=dry_run, version=next_version)
        dutils.indented_print(f"- Updated {settings.changelogs.root} file")
    # Update next_version on version.txt
    version_file = settings.version_path
    version_file.write_text(f"{next_version}\n")
    dutils.indented_print(f"- Updated {version_file} file")
    # Update docker-compose.yml
    compose_file = settings.compose_path
    if compose_file.exists() and compose_file.is_file():
        contents = compose_file.read_text().replace(original_version, next_version)
        compose_file.write_text(contents)
        dutils.indented_print(f"- Updated {compose_file} file")
    else:
        dutils.indented_print("- No docker-compose.yml file to update")


def _step_release_backend(
    step_id: int,
    title: str,
    settings: t.RepositorySettings,
    original_version: str,
    next_version: str,
    dry_run: bool,
):
    utils.release_backend(settings, next_version, dry_run)
    dutils.indented_print(f"- Released {settings.backend.name}: {next_version}")


def _step_release_frontend(
    step_id: int,
    title: str,
    settings: t.RepositorySettings,
    original_version: str,
    next_version: str,
    dry_run: bool,
):
    next_version = vutils.convert_python_node_version(next_version)
    utils.release_frontend(settings, next_version, dry_run)
    dutils.indented_print(f"- Released {settings.frontend.name}: {next_version}")


def _step_update_git(
    step_id: int,
    title: str,
    settings: t.RepositorySettings,
    original_version: str,
    next_version: str,
    dry_run: bool,
):
    if not dry_run:
        repo = gitutils.repo_for_project(settings.root_path)
        gitutils.finish_release(repo, next_version)
        dutils.indented_print(f"- Created tag {next_version}")
    else:
        dutils.indented_print(f"- Skipped creating tag {next_version}")


def _step_gh_release(
    step_id: int,
    title: str,
    settings: t.RepositorySettings,
    original_version: str,
    next_version: str,
    dry_run: bool,
):
    if dry_run:
        dutils.indented_print("- Skipping GitHub release creation")
        return
    if ghutils.check_token(settings):
        msg = ghutils.create_release(settings, original_version, next_version)
        dutils.indented_print(msg)
    else:
        dutils.indented_print(
            "- Skipping GitHub release creation as you do not have a GITHUB_TOKEN"
            "environment variable set"
        )


@app.command()
def do(
    ctx: typer.Context,
    desired_version: Annotated[
        str,
        typer.Argument(
            help=(
                "Next version. Could be the version number, or "
                "a segment like: a, minor, major, rc"
            )
        ),
    ],
    dry_run: Annotated[bool, typer.Option(help="Is this a dry run?")] = False,
):
    """Release the packages in this mono repo."""
    settings: t.RepositorySettings = ctx.obj.settings
    original_version = settings.version

    dutils.print(f"\n[bold green]Release {settings.name}[/bold green]\n")
    next_version, error = _get_next_version(settings, original_version, desired_version)
    if error:
        dutils.print(error)
        typer.Exit(0)
        return

    steps = [
        ("Next version", _step_confirm_version),
        ("Display Changelog", _step_prepare_changelog),
        ("Update repository components", _step_update_repository),
        ("Release backend", _step_release_backend),
        ("Release frontend", _step_release_frontend),
        ("Commit changes, create tag", _step_update_git),
        ("Create GitHub release", _step_gh_release),
        ("Goodbye", _step_goodbye),
    ]
    total_steps = len(steps)
    for step_id, (title, func) in enumerate(steps, start=1):
        dutils.print(
            f"\n[bold green]{step_id}/{total_steps}[/bold green] [bold]{title}[/bold]"
        )
        func(step_id, title, settings, original_version, next_version, dry_run)
    raise typer.Exit(0)


@app.command()
def changelog(
    ctx: typer.Context,
):
    """Generate a draft of the final changelog."""
    settings: t.RepositorySettings = ctx.obj.settings
    original_version = settings.version
    # Changelog
    new_entries, _ = chgutils.update_changelog(
        settings, draft=True, version=original_version
    )
    dutils.print(f"{'=' * 50}\n{new_entries}\n{'=' * 50}")
