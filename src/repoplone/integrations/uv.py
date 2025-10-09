from .base import ExternalCommand
from packaging.version import Version as PyPIVersion

import os


class UV(ExternalCommand):
    command: str = "uv"
    default_index: str = "pypi.org"
    min_version: str = "0.8.15"

    def _sanity_version(self) -> str:
        """Check if the installed version of UV is compatible."""
        error = ""
        result = self._run("uv", ["--version"])
        stdout = result.stdout.strip().split(" ")
        # Parse a version number like `uv 0.8.15 (8473ecba1 2025-09-03)``
        version = PyPIVersion(stdout[1]) if stdout else None
        min_version = PyPIVersion(self.min_version)
        if not version or version < min_version:
            error = f"UV version {self.min_version} or higher is required."
        return error

    def _sanity_authenticated(self) -> str:
        """Try to validate if we are authenticated on pypi."""
        error = ""
        token = os.getenv("UV_PUBLISH_TOKEN")
        if not token:
            result = self._run("uv", ["auth", "token", self.default_index])
            if result.returncode:
                error = f"You are not authenticated to pypi using UV. {result.stderr}"
        return error

    def check_authentication(self) -> bool:
        """Check if we are authenticated on pypi."""
        error = self._sanity_authenticated()
        return not bool(error)

    def build(self) -> bool:
        """Build the package."""
        result = self._run(self.command, ["build"])
        if result.returncode:
            raise RuntimeError(f"UV build failed {result.stderr}")
        return True

    def publish(self) -> bool:
        """Build the package."""
        result = self._run(self.command, ["publish"])
        if result.returncode:
            raise RuntimeError(f"UV publish failed {result.stderr}")
        return True

    def run(self, publish: bool) -> bool:
        """Build the package."""
        self.sanity()
        # Build the package
        self.build()
        if publish:
            self.publish()
        return True
