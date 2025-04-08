from click.testing import CliRunner as __CliRunner
from hatch import cli


class CliRunner(__CliRunner):
    def __init__(self, command):
        super().__init__()
        self._command = command

    def __call__(self, *args, **kwargs):
        # Exceptions should always be handled
        kwargs.setdefault("catch_exceptions", False)

        return self.invoke(self._command, args, **kwargs)


def get_hatch() -> CliRunner:
    return CliRunner(cli.hatch)
