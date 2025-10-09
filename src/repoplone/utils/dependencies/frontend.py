from functools import cache
from pathlib import Path
from repoplone import _types as t
from typing import Any

import json
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


def _get_version_from_mrs_developer(
    frontend_path: Path, checkout: str = "core", package_name: str = "@plone/volto"
) -> str | None:
    """Update package version and run make install again."""
    mrs_developer_path = frontend_path / "mrs.developer.json"
    data = _load_json_file(mrs_developer_path)
    checkout_entry = data.get(checkout)
    if not checkout_entry:
        raise ValueError(f"No '{checkout}' entry found in mrs.developer.json")
    elif (package_ := checkout_entry["package"]) != package_name:
        raise ValueError(
            f"mrs.developer.json {checkout} package is {package_}, not {package_name}"
        )
    current_version = checkout_entry.get("tag")
    return current_version


def package_version(frontend_path: Path, package_name: str) -> str | None:
    """Return the version of a package."""
    if package_name == "@plone/volto":
        return _get_version_from_mrs_developer(frontend_path, package_name=package_name)
    pnpm_lock = frontend_path / "pnpm-lock.yaml"
    if not pnpm_lock.exists():
        return None
    deps = __get_project_dependencies(pnpm_lock)
    if version := deps.get(package_name):
        return version
    return None


def _load_json_file(path: Path) -> dict[str, Any]:
    """Load a JSON file and return its content as a dictionary."""
    return json.loads(path.read_text())


def _save_json_file(data: dict[str, Any], path: Path) -> None:
    """Load a JSON file and return its content as a dictionary."""
    path.write_text(json.dumps(data, indent=2))


def _update_version_mrs_developer(
    settings: t.RepositorySettings, package_name: str, version: str
) -> bool:
    """Update package version in mrs.developer.json."""
    frontend_package_path = settings.frontend.path
    # Package will be inside frontend/packages/<package>
    frontend_root_path = frontend_package_path.parent.parent
    mrs_developer_path = frontend_root_path / "mrs.developer.json"
    data = _load_json_file(mrs_developer_path)
    core_checkout = data.get("core")
    if not core_checkout:
        raise ValueError("No 'core' entry found in mrs.developer.json")
    elif (package_ := core_checkout["package"]) != package_name:
        raise ValueError(
            f"mrs.developer.json core package is {package_}, not {package_name}"
        )
    current_version = core_checkout.get("tag")
    if current_version != version:
        core_checkout["tag"] = version
        _save_json_file(data, mrs_developer_path)
        return True
    return False


def _update_version_package_json(
    settings: t.RepositorySettings, package_name: str, version: str
) -> bool:
    """Update package version and run make install again."""
    frontend_package_path = settings.frontend.path
    package_json_path = frontend_package_path / "package.json"
    data = _load_json_file(package_json_path)
    dependencies = data.get("dependencies", {})
    if package_name not in dependencies:
        raise ValueError(f"No '{package_name}' entry found in package.json")
    current_version = dependencies.get(package_name)
    if current_version != version:
        dependencies[package_name] = version
        _save_json_file(data, package_json_path)
        return True
    return False


def update_base_package(
    settings: t.RepositorySettings, package_name: str, version: str
) -> bool:
    """Update package version."""
    func = (
        _update_version_mrs_developer
        if package_name == "@plone/volto"
        else _update_version_package_json
    )
    status = func(settings, package_name, version)
    return status
