from repoplone.exceptions import RepoPloneException

import sys
import typer


class RepoPlone(typer.Typer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        try:
            super().__call__(*args, **kwargs)
        except typer.Exit as exc:
            sys.exit(exc.exit_code)
        except RepoPloneException as exc:
            typer.echo(f"Error: {exc.message}", err=True)
            sys.exit(1)
        except Exception as exc:
            raise exc
