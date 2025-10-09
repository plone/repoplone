from .base import ExternalCommand


class ReleaseIt(ExternalCommand):
    command: str = "npx release-it"

    base_args: tuple[str, ...] = ("--ci", "--no-git", "--no-github.release")

    dry_run: tuple[str, ...] = ("--dry-run", "--npm.skipChecks")
    publish_args: tuple[str, ...] = ("--plonePrePublish.publish",)

    def _sanity_authenticated(self) -> str:
        """Check if we have an authentication on NPM."""
        error = ""
        result = self._run("npm", ["whoami"])
        if result.returncode > 0:
            error = f"You are not authenticated to npm. {result.stderr}"
        return error

    def check_authentication(self) -> bool:
        """Check if we are authenticated on NPM."""
        error = self._sanity_authenticated()
        return not bool(error)

    def run(self, dry_run: bool, publish: bool, version: str) -> bool:
        """Build the package."""
        args = list(self.base_args)
        if dry_run:
            args.extend(list(self.dry_run))
        if publish:
            args.extend(list(self.publish_args))
        args.extend([f"-i {version}"])

        result = self._run(self.command, args)
        if result.returncode:
            raise RuntimeError(f"NPM publish failed {result.stderr}")
        return True
