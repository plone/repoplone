from functools import cache
from packaging.version import InvalidVersion
from packaging.version import Version

import requests


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


def get_pypi_package_versions(package: str) -> list[str]:
    """Get versions for a PyPi package."""
    url: str = f"https://pypi.org/pypi/{package}/json"
    resp = requests.get(url)  # noQA: S113
    data = resp.json()
    return list(data.get("releases").keys())


@cache
def package_versions(package_name: str = "Products.CMFPlone") -> list[str]:
    versions = sorted(get_pypi_package_versions(package_name))
    return versions


@cache
def plone_versions() -> list[str]:
    return package_versions("Products.CMFPlone")


def latest_package_version(package_name: str) -> str | None:
    """Latest version for base package."""
    versions = package_versions(package_name)
    return version_latest(versions, allow_prerelease=True)
