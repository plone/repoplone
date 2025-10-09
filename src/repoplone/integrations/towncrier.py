from .base import ExternalCommand
from packaging.version import Version as PyPIVersion
from pathlib import Path


class Towncrier(ExternalCommand):
    command: str = "uvx towncrier"
    min_version: str = "25.8.0"

    def _sanity_version(self) -> str:
        """Check if the installed version of UV is compatible."""
        error = ""
        result = self._run(self.command, ["--version"])
        stdout = result.stdout.strip().split(" ")
        # Parse a version number like `towncrier, version 25.8.0``
        version = PyPIVersion(stdout[-1]) if stdout else None
        min_version = PyPIVersion(self.min_version)
        if not version or version < min_version:
            error = f"Towncrier version {self.min_version} or higher is required."
        return error

    def _build(self, args: list[str]) -> str:
        """Update changelog."""
        result = self._run(self.command, args)
        if result.returncode:
            raise RuntimeError(f"Towncrier failed {result.stderr}")
        return result.stdout

    def _draft(self, args: list[str]) -> str:
        """Build the package."""
        args.append("--draft")
        return self._build(args)

    def run(self, config: Path, name: str, version: str, draft: bool = True) -> str:
        """Build the package."""
        self.sanity()
        # Prepare arguments
        args: list[str] = [
            "build",
            "--config",
            f"{config}",
            "--yes",
            "--name",
            f"'{name}'",
            "--version",
            version,
        ]
        if draft:
            return self._draft(args)
        return self._build(args)
