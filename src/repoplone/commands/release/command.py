from .steps import check_confirm
from .steps import get_next_version
from .steps import get_steps
from repoplone import _types as t
from repoplone.app import RepoPlone
from repoplone.utils import display as dutils
from repoplone.utils import release as utils
from typing import Annotated

import typer


app = RepoPlone()


NO_VERSION: str = "next"


def _preflight_check(settings: t.RepositorySettings) -> bool:
    """Check if the repository is ready for a release."""
    status: bool = True
    sanity = utils.sanity_check(settings)

    if sanity.warnings:
        dutils.print("\n[bold yellow]Warnings:[/bold yellow]")
        for warning in sanity.warnings:
            dutils.print(f"- [yellow]{warning}[/yellow]")

    if sanity.errors:
        dutils.print("\n[bold red]Errors:[/bold red]")
        for error in sanity.errors:
            dutils.print(f"- [red]{error}[/red]")
        raise typer.Exit(1)

    if sanity.warnings:
        status = check_confirm("Do you want to continue the release?")
    return status


def _prompt_version_semver(original_version: str, total_steps: int) -> str:
    """Prompt the user for the next version."""
    step_index = 1
    prompt_message = (
        f"\n[bold green]{step_index:02d}/{total_steps:02d}[/bold green] "
        "[bold]Select the next version[/bold]"
    )
    options = utils.options_next_version(original_version)
    answer = dutils.choice(prompt_message, options)
    return answer


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    desired_version: Annotated[
        str,
        typer.Argument(
            help=(
                "Next version. Could be the version number, or "
                "a segment like: a, minor, major, rc"
            ),
        ),
    ] = NO_VERSION,
    dry_run: Annotated[bool, typer.Option(help="Is this a dry run?")] = False,
):
    """Release the packages in this repository."""
    settings: t.RepositorySettings = ctx.obj.settings
    dutils.print(f"\n[bold green]Release {settings.name}[/bold green]")
    if not _preflight_check(settings):
        raise typer.Exit(0)

    steps = get_steps()
    total_steps = len(steps)

    original_version = settings.version
    version_format = settings.version_format
    desired_version = desired_version if desired_version != NO_VERSION else ""
    start_step = 1
    if version_format == "calver" and not desired_version:
        desired_version = version_format
    elif not desired_version:
        start_step += 1
        total_steps += 1
        desired_version = _prompt_version_semver(original_version, total_steps)

    next_version, error = get_next_version(settings, original_version, desired_version)
    if error:
        dutils.print(error)
        typer.Exit(0)
        return

    for step_index, step in enumerate(steps, start=start_step):
        dutils.print(
            f"\n[bold green]{step_index:02d}/{total_steps:02d}[/bold green] "
            f"[bold]{step.title}[/bold]"
        )
        step.func(
            step_index, step.title, settings, original_version, next_version, dry_run
        )
    raise typer.Exit(0)
