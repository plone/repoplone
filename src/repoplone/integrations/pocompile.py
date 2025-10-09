from .base import ExternalCommand
from repoplone.utils._path import change_cwd
from zest.pocompile import compile as pocompile


class PoCompile(ExternalCommand):
    command: str = "pocompile"
    directory: str = "./src"

    def run(self) -> bool:
        """Generate .mo files."""
        try:
            with change_cwd(self.cwd):
                pocompile.compile_po(self.directory)
        except Exception as e:
            raise RuntimeError(
                f"There was an error while running pocompile: {e}"
            ) from e
        return True
