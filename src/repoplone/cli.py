from repoplone import __version__
from repoplone import _types as t
from repoplone.commands.dependencies import app as app_deps
from repoplone.commands.release import app as app_release
from repoplone.commands.versions import app as app_versions
from repoplone.settings import get_settings
from typing import Annotated

import typer


app = typer.Typer(no_args_is_help=True)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Annotated[
        bool, typer.Option(help="Report the version of this app.")
    ] = False,
):
    """Welcome to Plone Distribution Helper."""
    try:
        settings = get_settings()
    except RuntimeError:
        typer.echo("Not running inside a mono repo.")
        raise typer.Exit() from None
    if version:
        typer.echo(f"repoplone {__version__}")
    else:
        ctx_obj = t.CTLContextObject(settings=settings)
        ctx.obj = ctx_obj
        ctx.ensure_object(t.CTLContextObject)


app.add_typer(
    app_release, name="release", no_args_is_help=True, help="Release mono repo packages"
)
app.add_typer(
    app_deps,
    name="deps",
    no_args_is_help=True,
    help="Check and manage dependencies",
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
