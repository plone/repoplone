from functools import cache
from packaging.version import InvalidVersion
from packaging.version import Version
from repoplone import _types as t
from repoplone import exceptions
from repoplone.utils._requests import get_remote_data


def is_valid_version(
    version: Version,
    min_version: Version | None = None,
    max_version: Version | None = None,
    allow_prerelease: bool = False,
) -> bool:
    """Check if version is valid."""
    status = True
    if version.is_prerelease:
        status = allow_prerelease
    if status and min_version:
        status = version >= min_version
    if status and max_version:
        status = version < max_version
    return status


def version_latest(
    versions: list[str],
    min_version: str | None = None,
    max_version: str | None = None,
    allow_prerelease: bool = False,
) -> str | None:
    min_version_ = Version(min_version) if min_version else None
    max_version_ = Version(max_version) if max_version else None
    versions_ = []
    for version in versions:
        try:
            v_info = (Version(version.replace("v", "")), version)
        except InvalidVersion:
            continue
        versions_.append(v_info)

    versions_ = sorted(versions_, reverse=True)
    valid = [
        (version, raw_version)
        for version, raw_version in versions_
        if is_valid_version(version, min_version_, max_version_, allow_prerelease)
    ]
    return valid[0][1] if valid else None


def get_npm_package_versions(package: str) -> list[str]:
    """Get versions for a npm package."""
    url: str = f"https://registry.npmjs.org/{package}"
    resp = get_remote_data(
        url, headers={"Accept": "application/vnd.npm.install-v1+json"}
    )
    data = resp.json()
    return list(data["dist-tags"].values())


def get_pypi_package_versions(package: str) -> list[str]:
    """Get versions for a PyPi package."""
    url: str = f"https://pypi.org/pypi/{package}/json"
    resp = get_remote_data(url)
    data = resp.json()
    return list(data.get("releases").keys())


@cache
def pypi_package_versions(package_name: str = "Products.CMFPlone") -> list[str]:
    try:
        versions = sorted(get_pypi_package_versions(package_name))
    except exceptions.RepoPloneExternalException as exc:
        raise exceptions.RepoPloneExternalException(
            f"Failed to fetch versions for package {package_name}: {exc}"
        ) from exc
    return versions


@cache
def npm_package_versions(package_name: str = "@plone/volto") -> list[str]:
    try:
        versions = sorted(get_npm_package_versions(package_name))
    except exceptions.RepoPloneExternalException as exc:
        raise exceptions.RepoPloneExternalException(
            f"Failed to fetch versions for package {package_name}: {exc}"
        ) from exc
    return versions


@cache
def plone_versions() -> list[str]:
    return pypi_package_versions("Products.CMFPlone")


def python_latest_package_version(package_name: str) -> str | None:
    """Latest version for base package."""
    versions = pypi_package_versions(package_name)
    return version_latest(versions, allow_prerelease=True)


def node_latest_package_version(package_name: str) -> str | None:
    """Latest version for base package."""
    versions = npm_package_versions(package_name)
    return version_latest(versions, allow_prerelease=True)


def check_backend_base_package(settings: t.RepositorySettings) -> tuple[str, str, str]:
    """Check latest version of the backend base package."""
    package_name: str = settings.backend.base_package
    if not settings.backend.managed_by_uv:
        raise RuntimeError(
            "Backend version check is only available for installations managed by uv."
        )
    current = settings.backend.base_package_version

    latest_version = python_latest_package_version(package_name) or "unknown"
    return package_name, current, latest_version


def check_frontend_base_package(settings: t.RepositorySettings) -> tuple[str, str, str]:
    """Check latest version of the frontend base package."""
    package_name: str = settings.frontend.base_package
    current = settings.frontend.base_package_version
    latest_version = node_latest_package_version(package_name) or "unknown"
    return package_name, current, latest_version
