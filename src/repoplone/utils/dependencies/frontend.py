from functools import cache
from pathlib import Path

import re
import yaml


_PATTERN = re.compile(r"^(?P<package>@?[^@]*)@(?P<version>.*)$")


def _parse_dependencies(data: dict) -> dict[str, str]:
    """Return the current package dependencies."""
    dependencies = {}
    raw_dependencies = data.get("packages", {})
    for key in raw_dependencies:
        match = re.match(_PATTERN, key)
        if match:
            package = match.groupdict()["package"]
            version = match.groupdict()["version"]
            dependencies[package] = version
    return dependencies


@cache
def __get_project_dependencies(lock_path: Path) -> dict[str, str]:
    data = yaml.safe_load(lock_path.read_text())
    deps = _parse_dependencies(data)
    return deps


def package_version(frontend_path: Path, package_name: str) -> str | None:
    """Return the version of a package."""
    pnpm_lock = frontend_path / "pnpm-lock.yaml"
    if not pnpm_lock.exists():
        return None
    deps = __get_project_dependencies(pnpm_lock)
    if version := deps.get(package_name):
        return version
    return None
