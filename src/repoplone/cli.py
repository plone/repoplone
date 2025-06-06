from repoplone import __version__
from repoplone import _types as t
from repoplone.app import RepoPlone
from repoplone.commands.changelog import app as app_changelog
from repoplone.commands.dependencies import app as app_deps
from repoplone.commands.release import app as app_release
from repoplone.commands.settings import app as app_settings
from repoplone.commands.versions import app as app_versions
from repoplone.settings import get_settings
from typing import Annotated

import typer


app = RepoPlone(no_args_is_help=True)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Annotated[
        bool, typer.Option(help="Report the version of this app.")
    ] = False,
):
    """Welcome to Plone Repository Helper."""
    try:
        settings = get_settings()
    except RuntimeError:
        typer.echo("Did not find a repository.toml file.")
        raise typer.Exit() from None
    if version:
        typer.echo(f"repoplone {__version__}")
    else:
        ctx_obj = t.CTLContextObject(settings=settings)
        ctx.obj = ctx_obj
        ctx.ensure_object(t.CTLContextObject)


app.add_typer(
    app_changelog,
    name="changelog",
    no_args_is_help=False,
    help="Displays a draft of Change log entries",
)
app.add_typer(
    app_release,
    name="release",
    no_args_is_help=True,
    help="Release packages in this repository",
)
app.add_typer(
    app_deps,
    name="deps",
    no_args_is_help=True,
    help="Check and manage dependencies",
)
app.add_typer(
    app_settings,
    name="settings",
    no_args_is_help=True,
    help="Manage settings for a repository",
)
app.add_typer(
    app_versions,
    name="versions",
    no_args_is_help=True,
    help="Display version information about this repository",
)


def cli():
    app()


__all__ = ["cli"]
