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
    ],
    dry_run: Annotated[bool, typer.Option(help="Is this a dry run?")] = False,
):
    """Release the packages in this repository."""
    settings: t.RepositorySettings = ctx.obj.settings
    original_version = settings.version
    version_format = settings.version_format
    desired_version = desired_version if desired_version != NO_VERSION else ""
    if version_format == "calver" and not desired_version:
        desired_version = version_format
    if not desired_version:
        dutils.print("You must provide the desired version.")
        raise typer.Exit(1)

    dutils.print(f"\n[bold green]Release {settings.name}[/bold green]")
    if not _preflight_check(settings):
        raise typer.Exit(0)

    next_version, error = get_next_version(settings, original_version, desired_version)
    if error:
        dutils.print(error)
        typer.Exit(0)
        return

    steps = get_steps()
    total_steps = len(steps)
    for step_index, step in enumerate(steps, start=1):
        dutils.print(
            f"\n[bold green]{step_index}/{total_steps}[/bold green] "
            f"[bold]{step.title}[/bold]"
        )
        step.func(
            step_index, step.title, settings, original_version, next_version, dry_run
        )
    raise typer.Exit(0)
