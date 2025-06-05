from collections.abc import Callable
from dynaconf import Dynaconf
from dynaconf.utils.boxing import DynaBox
from pathlib import Path
from repoplone import _types as t
from repoplone.utils import versions
from repoplone.utils.dependencies import frontend as frontend_utils
from repoplone.utils.dependencies import pyproject as pyproject_utils


PYPROJECT_TOML = "pyproject.toml"


def get_changelogs(
    root_changelog: Path, backend: t.Package, frontend: t.Package
) -> t.Changelogs:
    return t.Changelogs(root_changelog, backend.changelog, frontend.changelog)


def get_towncrier_settings(
    backend: t.Package, frontend: t.Package, repository: dict
) -> t.TowncrierSettings:
    sections = []
    raw_sections = [
        ("backend", "Backend", backend.towncrier),
        ("frontend", "Frontend", frontend.towncrier),
    ]
    if repository:
        section = (
            "repository",
            repository["section"],
            Path(repository["settings"]).resolve(),
        )
        raw_sections.append(section)
    sections = [t.TowncrierSection(*info) for info in raw_sections]
    return t.TowncrierSettings(sections=sections)


def get_pyproject(settings: t.RepositorySettings) -> Path | None:
    """Return the pyproject.toml for a monorepo."""
    paths = [
        settings.root_path,
        settings.backend.path,
    ]
    for base_path in paths:
        path = base_path / PYPROJECT_TOML
        if path.exists():
            return path
    return None


def get_next_version(settings: t.RepositorySettings) -> str:
    version_file = settings.version_path
    cur_version = version_file.read_text().strip()
    next_version = cur_version.replace(".dev", "")
    return next_version


def _get_package_info(
    root_path: Path,
    package_settings: DynaBox,
    default_base_package: str,
    version_func: Callable,
) -> dict:
    """Return package information for the frontend."""
    path = (root_path / package_settings.path).resolve()
    changelog = (root_path / package_settings.changelog).resolve()
    towncrier = (root_path / package_settings.towncrier_settings).resolve()
    version = version_func(path)
    publish = bool(package_settings.get("publish", True))
    base_package = package_settings.get("base_package", default_base_package)
    package_name = package_settings.name
    payload = {
        "enabled": bool(package_name),
        "name": package_name,
        "path": path,
        "base_package": base_package,
        "version": version,
        "publish": publish,
        "changelog": changelog,
        "towncrier": towncrier,
    }
    return payload


def get_backend(root_path: Path, raw_settings: Dynaconf) -> t.BackendPackage:
    """Return package information for the backend."""
    package_settings = raw_settings.backend.package
    version_func = versions.get_backend_version
    default_base_package: str = "Products.CMFPlone"
    package_info = _get_package_info(
        root_path, package_settings, default_base_package, version_func
    )
    pyproject_toml = package_info["path"] / "pyproject.toml"
    package_info["managed_by_uv"] = pyproject_utils.managed_by_uv(pyproject_toml)
    package_info["base_package_version"] = pyproject_utils.current_base_package(
        pyproject_toml,
        package_info["base_package"],
    )
    return t.BackendPackage(**package_info)


def get_frontend(root_path: Path, raw_settings: Dynaconf) -> t.FrontendPackage:
    """Return package information for the frontend."""
    package_settings = raw_settings.frontend.package
    version_func = versions.get_frontend_version
    default_base_package: str = "@plone/volto"
    package_info = _get_package_info(
        root_path, package_settings, default_base_package, version_func
    )
    path = root_path / "frontend"
    package_info["base_package_version"] = frontend_utils.package_version(
        path,
        package_info["base_package"],
    )
    package_info["volto_version"] = frontend_utils.package_version(
        path,
        "@plone/volto",
    )
    return t.FrontendPackage(**package_info)
