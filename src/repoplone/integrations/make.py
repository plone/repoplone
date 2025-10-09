from .base import ExternalCommand


class Make(ExternalCommand):
    command: str = "make"

    def run(self, target: str) -> bool:
        """Run a Makefile target."""
        self.sanity()
        result = self._run(self.command, [target])
        if result.returncode:
            raise RuntimeError(
                f"There was an error while running make: {result.stderr}"
            )
        return True
