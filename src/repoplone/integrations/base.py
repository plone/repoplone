from pathlib import Path

import subprocess


class ExternalCommand:
    command: str
    cwd: Path

    def __init__(self, cwd: Path | None = None):
        if cwd is None:
            cwd = Path.cwd()
        self.cwd = cwd

    def _run(self, command: str, args: list[str]):
        cmd = [command, *args]
        result = subprocess.run(  # noQA: S602
            " ".join(cmd),
            capture_output=True,
            text=True,
            shell=True,
            cwd=self.cwd,
        )
        return result

    def _check_exists(self) -> str:
        """Check if command exists."""
        result = self._run(self.command, ["--version"])
        error = f"Command {self.command} not found" if result.returncode else ""
        return error

    def sanity(self) -> bool:
        """Run sanity checks."""
        errors: list[str] = []
        if self._check_exists():
            raise RuntimeError(f"Command not found: {self.command}")
        # Run all _sanity_ methods
        methods = [m for m in self.__dir__() if m.startswith("_sanity_")]
        for name in methods:
            method = getattr(self, name)
            error = method()
            if error:
                errors.append(error)
        if errors:
            raise RuntimeError(f"Sanity checks failed: {errors}")
        return True
