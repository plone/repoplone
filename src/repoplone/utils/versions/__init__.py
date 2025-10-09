from . import calver
from . import semver
from packaging.version import Version as PyPIVersion
from pathlib import Path
from repoplone import _types as t
from repoplone.utils._hatch import get_hatch
from repoplone.utils._path import change_cwd

import json
import re


VERSION_PATTERNS = (
    (r"^(a)(\d{1,2})", r"alpha.\2"),
    (r"^(b)(\d{1,2})", r"beta.\2"),
    (r"^(rc)(\d{1,2})", r"rc.\2"),
)


def convert_python_node_version(version: str) -> str:
    """Converts a PyPI version into a semver version

    :param ver: the PyPI version
    :return: a semver version
    :raises ValueError: if epoch or post parts are used
    """
    pypi_version = PyPIVersion(version)
    pre = None if not pypi_version.pre else "".join([str(i) for i in pypi_version.pre])
    if pre:
        for raw_pattern, replace in VERSION_PATTERNS:
            pattern = re.compile(raw_pattern)
            if re.search(pattern, pre):
                pre = re.sub(pattern, replace, pre)

    parts = list(pypi_version.release)
    if len(parts) == 2:
        parts.append(0)
    major, minor, patch = parts
    build = pypi_version.dev if pypi_version.dev else None
    version = str(semver.version_from_parts(major, minor, patch, pre, build))
    return version


def get_repository_version(settings: t.RepositorySettings) -> str:
    """Return the currect repository version."""
    version_path = settings.version_path
    return version_path.read_text().strip()


def get_backend_version(backend_path: Path) -> str:
    """Get the current version used by the backend."""
    hatch = get_hatch()
    with change_cwd(backend_path):
        result = hatch("version")
    return result.stdout.strip()


def get_frontend_version(frontend_package_path: Path) -> str:
    """Get the current version used by the frontend."""
    package_json = (frontend_package_path / "package.json").resolve()
    package_data = json.loads(package_json.read_text())
    return package_data["version"]


def update_backend_version(backend_path: Path, version: str) -> str:
    """Update version used by the backend."""
    hatch = get_hatch()
    with change_cwd(backend_path):
        result = hatch("version", version)
    if result.exit_code:
        raise RuntimeError("Error setting backend version")
    return get_backend_version(backend_path)


def update_frontend_version(frontend_package_path: Path, version: str) -> str:
    """Update version used by the frontend."""
    package_json = (frontend_package_path / "package.json").resolve()
    package_data = json.loads(package_json.read_text())
    package_data["version"] = version
    package_json.write_text(json.dumps(package_data, indent=2) + "\n")
    return get_frontend_version(frontend_package_path)


def next_version(desired_version: str, original_version: str) -> str:
    """Return the next version for this project."""
    if desired_version == "calver":
        return calver.next_version(desired_version, original_version)
    else:
        return semver.next_version(desired_version, original_version)


def report_cur_versions(settings: t.RepositorySettings) -> dict:
    sections: list[dict] = []
    cur_versions = {
        "repository": {"title": "Repository", "version": settings.version},
        "sections": sections,
    }
    for title, section in (
        ("Repository", settings),
        ("Backend", settings.backend),
        ("Frontend", settings.frontend),
    ):
        sections.append({
            "title": title,
            "name": section.name,
            "version": section.version,
        })
    return cur_versions


def report_deps_versions(settings: t.RepositorySettings) -> dict:
    sections: list[dict] = []
    cur_versions = {
        "repository": {"title": "Repository", "version": settings.version},
        "sections": sections,
    }
    rows = [
        (
            "Backend",
            settings.backend.base_package,
            settings.backend.base_package_version,
        ),
        (
            "Frontend",
            settings.frontend.base_package,
            settings.frontend.base_package_version,
        ),
    ]
    if settings.frontend.base_package != "@plone/volto":
        rows.append((
            "Frontend",
            "@plone/volto",
            settings.frontend.volto_version,
        ))

    for title, package, version in rows:
        sections.append({
            "title": title,
            "name": package,
            "version": version,
        })
    return cur_versions


def report_next_versions(settings: t.RepositorySettings):
    cur_version = settings.version
    version_format = settings.version_format
    versions = []
    if version_format == "calver":
        bumps = calver.bumps()
    elif version_format == "semver":
        bumps = semver.bumps()
    else:
        raise ValueError(f"Unknown version format {version_format}")
    for bump in bumps:
        nv = next_version(bump, cur_version)
        nv_semver = convert_python_node_version(nv)
        versions.append({
            "bump": bump,
            "repository": nv,
            "backend": nv,
            "frontend": nv_semver,
        })
    return versions
