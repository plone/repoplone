from ._git import repo_for_project
from ._git import repo_has_version
from ._hatch import get_hatch
from ._path import change_cwd
from .changelog import update_backend_changelog
from .versions import convert_python_node_version
from .versions import update_backend_version
from repoplone import _types as t
from repoplone import logger

import subprocess


def release_backend(settings: t.RepositorySettings, version: str, dry_run: bool):
    package = settings.backend
    # Update backend version
    hatch = get_hatch()
    if not dry_run:
        update_backend_version(package.path, version)
        update_backend_changelog(settings, dry_run, version)
    if not package.publish:
        return
    with change_cwd(settings.backend.path):
        logger.info(f"Build backend package {settings.backend.name}")
        # Build package
        hatch("build")
        if not dry_run:
            logger.info(f"Publish backend package {settings.backend.name}")
            hatch("publish")


def release_frontend(
    settings: t.RepositorySettings, project_version: str, dry_run: bool
):
    version = convert_python_node_version(project_version)
    action = "dry-release" if dry_run else "release"
    package = settings.frontend
    volto_addon_name = package.name
    logger.debug(f"Frontend: {action} for package {volto_addon_name} ({version})")
    cmd = "npx release-it --ci --no-git --no-github.release"
    if dry_run:
        # No need to check if we are authenticated on NPM
        cmd += " --dry-run --npm.skipChecks"
    elif not package.publish:
        cmd += "  --npm.skipChecks --no-npm.publish"
    cmd += f" -i {version}"
    result = subprocess.run(  # noQA: S602
        cmd,
        capture_output=True,
        text=True,
        shell=True,
        cwd=settings.frontend.path,
    )
    if result.returncode:
        raise RuntimeError(f"Frontend release failed {result.stderr}")


def valid_next_version(settings: t.RepositorySettings, next_version: str) -> bool:
    """Check if next version is valid."""
    is_valid = True
    repo = repo_for_project(settings.root_path)
    if repo:
        is_valid = not (repo_has_version(repo, next_version))
    return is_valid
