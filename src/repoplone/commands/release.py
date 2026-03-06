from repoplone import _types as t
from repoplone.app import RepoPlone
from repoplone.release.pipeline import ReleasePipeline
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
        status = dutils.check_confirm("Do you want to continue the release?")
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
    ] = NO_VERSION,
    dry_run: Annotated[bool, typer.Option(help="Is this a dry run?")] = False,
):
    """Release the packages in this repository."""
    settings: t.RepositorySettings = ctx.obj.settings
    dutils.print(f"\n[bold green]Release {settings.name}[/bold green]")
    if not _preflight_check(settings):
        raise typer.Exit(0)
    pipeline = ReleasePipeline(settings, dry_run, desired_version)
    try:
        pipeline()
    except RuntimeError as e:
        dutils.print(f"\n[bold red]Release failed: {e}[/bold red]")
        raise typer.Exit(1) from e

    raise typer.Exit(0)
