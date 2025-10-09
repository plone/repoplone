from repoplone import _types as t
from repoplone.app import RepoPlone
from repoplone.utils import display as dutils
from repoplone.utils import settings as utils

import json
import typer


app = RepoPlone()


@app.command()
def dump(ctx: typer.Context):
    """Dumps the current repository settings as JSON."""
    settings: t.RepositorySettings = ctx.obj.settings
    data = utils.settings_to_dict(settings)
    result = json.dumps(data, indent=2)
    dutils.print_json(result)
