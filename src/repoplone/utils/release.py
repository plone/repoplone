from ._git import repo_for_project
from ._git import repo_has_version
from ._github import check_token as gh_check_token
from ._path import change_cwd
from .changelog import update_backend_changelog
from .changelog import update_frontend_changelog
from .python_release import list_release_files
from .python_release import remove_release_files
from .versions import convert_python_node_version
from .versions import suggested_next_versions
from .versions import update_backend_version
from .versions import update_frontend_version
from dataclasses import dataclass
from repoplone import _types as t
from repoplone import logger
from repoplone.exceptions import RepoPloneExternalException
from repoplone.integrations.pocompile import PoCompile
from repoplone.integrations.release_it import ReleaseIt
from repoplone.integrations.uv import UV
from repoplone.utils.dependencies import versions as dep_versions


@dataclass
class ReleaseSanityCheckResult:
    errors: list[str]
    warnings: list[str]


def sanity_check(settings: t.RepositorySettings) -> ReleaseSanityCheckResult:
    """Check if components needed for release are propertly configured."""
    errors: list[str] = []
    warnings: list[str] = []
    # Authentication is per registry, not per package: check it once for each
    # family that publishes anything.
    python_packages = [
        package
        for package in settings.packages_for(t.FAMILY_PYTHON)
        if package.enabled and package.publish
    ]
    node_packages = [
        package
        for package in settings.packages_for(t.FAMILY_NODE)
        if package.enabled and package.publish
    ]
    if python_packages:
        uv = UV(python_packages[0].path)
        if not uv.check_authentication():
            errors.append("You are not authenticated to PyPi using UV.")
    if node_packages:
        release_it = ReleaseIt(node_packages[0].path)
        if not release_it.check_authentication():
            errors.append("You are not authenticated to NPM.")
    try:
        gh_token = gh_check_token(settings)
    except ValueError:
        warnings.append(
            "Could not find a valid origin pointing to a GitHub repository."
            " GitHub release will be skipped."
        )
    else:
        if not gh_token:
            warnings.append(
                "GITHUB_TOKEN is not present or does not have correct permissions."
                " GitHub release will be skipped."
            )
    return ReleaseSanityCheckResult(errors=errors, warnings=warnings)


def already_published(package: t.Package, version: str) -> bool:
    """Report whether a registry already carries a version of a package.

    Restarting a release with ``--start-step`` re-runs a whole step, and a
    step now covers every package of its family. Without this check the
    packages that reached their registry before the failure would be uploaded
    again, and fail -- turning a restart into a second failure rather than a
    resumption.

    A registry that cannot be reached answers ``False``: publishing and
    letting the registry reject a duplicate is a better failure than skipping
    a package that was never published.

    :param package: Package about to be published.
    :param version: Version about to be published.
    :returns: Whether that version is already on the registry.
    """
    lookup = (
        dep_versions.pypi_package_versions
        if package.family == t.FAMILY_PYTHON
        else dep_versions.npm_package_versions
    )
    try:
        published = lookup(package.name)
    except RepoPloneExternalException:
        return False
    return version in published


def release_backend(
    settings: t.RepositorySettings,
    package: t.Package,
    version: str,
    dry_run: bool,
):
    """Release one backend package.

    :param settings: Repository settings.
    :param package: Backend package to release.
    :param version: Version to release.
    :param dry_run: Whether to skip every write and upload.
    """
    package_name = package.name
    package_path = package.path
    if package.publish and not dry_run and already_published(package, version):
        logger.info(f"Skip {package_name} {version}: already published to PyPI")
        return
    # Compile .po files to .mo files
    pocompile = PoCompile(package_path)
    pocompile.run()
    # Update backend version
    uv = UV(package_path)
    if not dry_run:
        update_backend_version(package_path, version)
        update_backend_changelog(settings, package, dry_run, version)
    if not package.publish:
        return
    with change_cwd(package_path):
        logger.info(f"Build backend package {package_name}")
        if not dry_run:
            # Clean up dist folder
            existing_files = list_release_files()
            logger.debug(f"Found {len(existing_files)} files from previous builds")
            remove_release_files()

        # Build package using UV
        uv.build()
        if not dry_run:
            existing_files = list_release_files(version=version)
            logger.info(f"Publish backend package {package_name}")
            debug_msg = ", ".join([file.name for file in existing_files])
            logger.debug(f" - Files to be uploaded {debug_msg}")
            uv.publish()


def release_frontend(
    settings: t.RepositorySettings,
    package: t.Package,
    project_version: str,
    dry_run: bool,
):
    """Release one frontend package.

    :param settings: Repository settings.
    :param package: Frontend package to release.
    :param project_version: Repository version, converted to a node version.
    :param dry_run: Whether to skip every write and upload.
    """
    version = convert_python_node_version(project_version)
    should_publish = package.publish
    volto_addon_name = package.name
    package_path = package.path
    action = "dry-release" if dry_run else "release"
    logger.debug(f"Frontend: {action} for package {volto_addon_name} ({version})")
    if should_publish and not dry_run and already_published(package, version):
        # Skip the package whole: release-it would re-tag it, and rebuilding
        # the changelog with its news fragments already consumed would add a
        # second, empty entry.
        logger.info(f"Skip {volto_addon_name} {version}: already published to npm")
        return
    if not should_publish and not dry_run:
        # Just update version and changelog
        update_frontend_version(package_path, version)
        update_frontend_changelog(settings, package, dry_run, version)
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


def options_next_version(original_version: str) -> list[dict[str, str]]:
    """Return the list of options for the next version."""
    raw_options = suggested_next_versions(original_version)
    options = []
    for option in raw_options:
        key, value = next(iter(option.items()))
        options.append({key: f"{value} ({key})"})
    return options
