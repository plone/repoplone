from click.testing import CliRunner as __CliRunner
from click.testing import Result
from hatch import cli

import contextlib


class CliRunner(__CliRunner):
    def __init__(self, command):
        super().__init__()
        self._command = command

    def __call__(self, *args, **kwargs) -> Result:
        # Exceptions should always be handled
        kwargs.setdefault("catch_exceptions", False)
        # Suppress output and just return the result
        with contextlib.redirect_stdout(None), contextlib.redirect_stderr(None):
            result = self.invoke(self._command, args, **kwargs)
        return result


def get_hatch() -> CliRunner:
    return CliRunner(cli.hatch)
