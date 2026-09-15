from functools import cache
from pathlib import Path
from repoplone import _types as t
from repoplone.utils import versions as v_utils
from typing import Any

import json
import re
import yaml


_PATTERN = re.compile(r"^(?P<package>@?[^@]*)@(?P<version>.*)$")


def _load_mrs_developer(frontend_path: Path) -> dict[str, t.MrsDeveloperEntry]:
    """Load mrs.developer.json file."""
    mrs_developer_path = frontend_path / "mrs.developer.json"
    data = _load_json_file(mrs_developer_path)
    return data


def _save_mrs_developer(frontend_path: Path, data: dict[str, t.MrsDeveloperEntry]):
    """Save mrs.developer.json file."""
    mrs_developer_path = frontend_path / "mrs.developer.json"
    _save_json_file(data, mrs_developer_path)


def _get_entry_mrs_developer(
    data: dict[str, t.MrsDeveloperEntry], package_name: str
) -> t.MrsDeveloperEntry:
    """Get package entry from mrs.developer.json data."""
    for entry in data.values():
        if entry.get("package") == package_name:
            return entry
    raise ValueError(
        f"No entry found in mrs.developer.json for package '{package_name}'"
    )


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


def _parse_version_from_mrs_developer(
    checkout_entry: t.MrsDeveloperEntry, transform: bool = True
) -> str | None:
    """Parse version from mrs.developer.json."""
    version: str | None = checkout_entry.get("tag")
    if transform and version:
        version = v_utils.semver_from_tag(version)
    return version


def _get_version_from_mrs_developer(
    frontend_path: Path, package_name: str = "@plone/volto", transform: bool = True
) -> str | None:
    """Get package version from mrs.developer.json."""
    data = _load_mrs_developer(frontend_path=frontend_path)
    checkout_entry: t.MrsDeveloperEntry = _get_entry_mrs_developer(data, package_name)
    return _parse_version_from_mrs_developer(checkout_entry, transform=transform)


def get_core_tag(frontend_path: Path) -> str | None:
    """Return the raw ``@plone/volto`` checkout tag from mrs.developer.json.

    Unlike :func:`package_version`, the tag is returned verbatim (no semver
    normalization), as it is meant to be recorded as-is.
    """
    try:
        return _get_version_from_mrs_developer(
            frontend_path, package_name="@plone/volto", transform=False
        )
    except ValueError:
        return None


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
    # Check if package is in mrs_developer.json
    version = _get_version_from_mrs_developer(frontend_path, package_name=package_name)
    return version


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
    data = _load_mrs_developer(frontend_path=frontend_root_path)
    checkout_entry: t.MrsDeveloperEntry = _get_entry_mrs_developer(data, package_name)
    current_version_raw = _parse_version_from_mrs_developer(
        checkout_entry, transform=False
    )
    current_version = _parse_version_from_mrs_developer(checkout_entry, transform=True)
    if current_version != version:
        if current_version_raw != current_version:
            # Use Python version format
            version = v_utils.convert_node_python_version(version)
        checkout_entry["tag"] = version
        _save_mrs_developer(frontend_root_path, data)
        return True
    return False


def update_core_tag_mrs_developer(frontend_root: Path, volto_version: str) -> bool:
    """Update the ``@plone/volto`` checkout tag in mrs.developer.json.

    Used to keep the Volto core checked out by mrs-developer aligned with the
    ``volto_version`` enforced by the distribution. Returns True when the file
    was changed.
    """
    data = _load_mrs_developer(frontend_path=frontend_root)
    try:
        entry = _get_entry_mrs_developer(data, "@plone/volto")
    except ValueError:
        return False
    if entry.get("tag") != volto_version:
        entry["tag"] = volto_version
        _save_mrs_developer(frontend_root, data)
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
    func = _update_version_package_json
    frontend_root_path = settings.frontend.path.parent.parent
    try:
        _get_version_from_mrs_developer(frontend_root_path, package_name=package_name)
    except ValueError:
        pass
    else:
        func = _update_version_mrs_developer
    status = func(settings, package_name, version)
    return status
