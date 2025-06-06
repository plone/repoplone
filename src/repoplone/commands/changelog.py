from repoplone import _types as t
from repoplone.app import RepoPlone
from repoplone.utils import changelog as chgutils
from repoplone.utils import display as dutils

import typer


app = RepoPlone()


@app.callback(invoke_without_command=True)
def main(
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
