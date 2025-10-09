from ._git import repo_for_project
from ._git import repo_has_version
from ._github import check_token as gh_check_token
from ._path import change_cwd
from .changelog import update_backend_changelog
from .changelog import update_frontend_changelog
from .versions import convert_python_node_version
from .versions import update_backend_version
from .versions import update_frontend_version
from dataclasses import dataclass
from repoplone import _types as t
from repoplone import logger
from repoplone.integrations.pocompile import PoCompile
from repoplone.integrations.release_it import ReleaseIt
from repoplone.integrations.uv import UV


@dataclass
class ReleaseSanityCheckResult:
    errors: list[str]
    warnings: list[str]


def sanity_check(settings: t.RepositorySettings) -> ReleaseSanityCheckResult:
    """Check if components needed for release are propertly configured."""
    errors: list[str] = []
    warnings: list[str] = []
    backend_package = settings.backend
    frontend_package = settings.frontend
    if backend_package.publish:
        uv = UV(backend_package.path)
        if not uv.check_authentication():
            errors.append("You are not authenticated to PyPi using UV.")
    if frontend_package.publish:
        release_it = ReleaseIt(frontend_package.path)
        if not release_it.check_authentication():
            errors.append("You are not authenticated to NPM.")
    if not gh_check_token(settings):
        warnings.append(
            "GITHUB_TOKEN is not present or does not have correct permissions."
            " GitHub release will be skipped."
        )
    return ReleaseSanityCheckResult(errors=errors, warnings=warnings)


def release_backend(settings: t.RepositorySettings, version: str, dry_run: bool):
    package = settings.backend
    package_name = package.name
    package_path = package.path
    # Compile .po files to .mo files
    pocompile = PoCompile(package_path)
    pocompile.run()
    # Update backend version
    uv = UV(package_path)
    if not dry_run:
        update_backend_version(package_path, version)
        update_backend_changelog(settings, dry_run, version)
    if not package.publish:
        return
    with change_cwd(package_path):
        logger.info(f"Build backend package {package_name}")
        # Build package using UV
        uv.build()
        if not dry_run:
            logger.info(f"Publish backend package {package_name}")
            uv.publish()


def release_frontend(
    settings: t.RepositorySettings, project_version: str, dry_run: bool
):
    version = convert_python_node_version(project_version)
    should_publish = settings.frontend.publish
    package = settings.frontend
    volto_addon_name = package.name
    package_path = package.path
    action = "dry-release" if dry_run else "release"
    logger.debug(f"Frontend: {action} for package {volto_addon_name} ({version})")
    if not should_publish and not dry_run:
        # Just update version and changelog
        update_frontend_version(package_path, version)
        update_frontend_changelog(settings, dry_run, version)
    else:
        # Use release-it to release and publish
        release_it = ReleaseIt(package_path)
        release_it.run(dry_run=dry_run, publish=should_publish, version=version)


def valid_next_version(settings: t.RepositorySettings, next_version: str) -> bool:
    """Check if next version is valid."""
    is_valid = True
    repo = repo_for_project(settings.root_path)
    if repo:
        is_valid = not (repo_has_version(repo, next_version))
    return is_valid
