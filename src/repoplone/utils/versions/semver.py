from hatchling.version.scheme import standard
from semver import Version


BUMPS = [
    "release",
    "major",
    "minor",
    "micro",
    "patch",
    "fix",
    "a",
    "b",
    "rc",
    "post",
    "dev",
]


def bumps() -> list[str]:
    """Return the list of supported version bumps."""
    return BUMPS


def next_version(desired_version: str, original_version: str) -> str:
    """Return the next version for this project.

    desired_version could be either a full version or one of the
    version segments detailed here: https://hatch.pypa.io/1.12/version/#updating
    """
    scheme = standard.StandardScheme("", {})
    next_version = scheme.update(desired_version, original_version, {})
    return next_version


def version_from_parts(
    major: int, minor: int, patch: int, pre: str | None = None, build: int | None = None
) -> str:
    """Return a semver version from its parts."""
    pre = pre if pre else None
    build = build if build else None
    version = str(Version(major, minor, patch, prerelease=pre, build=build))
    return version
