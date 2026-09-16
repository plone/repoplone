from collections.abc import Callable
from dynaconf import Dynaconf
from dynaconf.utils.boxing import DynaBox
from pathlib import Path
from repoplone import _types as t
from repoplone import defaults
from repoplone.utils import versions
from repoplone.utils._path import frontend_root
from repoplone.utils.dependencies import frontend as frontend_utils
from repoplone.utils.dependencies import pyproject as pyproject_utils

import tomlkit


PYPROJECT_TOML = "pyproject.toml"


def get_changelogs(
    root_changelog: Path, backend: t.Package, frontend: t.Package
) -> t.Changelogs:
    backend_changelog = backend.changelog if backend.enabled else root_changelog
    frontend_changelog = frontend.changelog if frontend.enabled else root_changelog
    return t.Changelogs(root_changelog, backend_changelog, frontend_changelog)


#: Headings spec 1 gives the two family sections. Spec 2 uses the package name.
LEGACY_SECTION_NAMES: dict[str, str] = {
    t.FAMILY_PYTHON: "Backend",
    t.FAMILY_NODE: "Frontend",
}


def _section_id(package: t.Package) -> str:
    """Return the towncrier section id of a package.

    The primary package of a family keeps the family's own id, so
    ``settings.towncrier.backend`` resolves the way it always has.

    :param package: The package.
    :returns: The section id.
    """
    if package.primary:
        return package.family
    return f"{package.family}:{package.name}"


def _section_name(package: t.Package, spec_version: int) -> str:
    """Return the heading a package gets in the repository changelog.

    An explicit ``section`` always wins. Otherwise spec 2 uses the package
    name, which is the only thing that reads well once a family holds several
    packages, while spec 1 keeps ``Backend`` and ``Frontend`` so upgrading
    repoplone never rewrites a project's changelog headings.

    :param package: The package.
    :param spec_version: Spec version of the file.
    :returns: The heading.
    """
    if package.section:
        return package.section
    if spec_version == 1:
        return LEGACY_SECTION_NAMES.get(package.family, package.name)
    return package.name


def get_towncrier_settings(
    root_path: Path,
    packages: list[t.Package],
    repository: dict,
    spec_version: int = 1,
) -> t.TowncrierSettings:
    """Return the towncrier sections of a repository, in document order.

    :param root_path: Repository root.
    :param packages: Every package declared in the file.
    :param repository: The ``[repository.towncrier]`` table.
    :param spec_version: Spec version of the file.
    :returns: The towncrier settings.
    """
    sections = [
        t.TowncrierSection(
            _section_id(package),
            _section_name(package, spec_version),
            package.towncrier,
            package.changelog,
        )
        for package in packages
        if package.enabled
    ]
    if repository and (towncrier := repository.get("settings", "")):
        path: Path = root_path / towncrier
        sections.append(
            t.TowncrierSection("repository", repository["section"], path.resolve())
        )
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
    package_type: str,
    version_func: Callable,
) -> dict:
    """Return the fields shared by every package, whatever its type.

    :param root_path: Repository root.
    :param package_settings: Raw package table read from ``repository.toml``.
    :param package_type: Canonical package type.
    :param version_func: Callable reading the current version from the package.
    :returns: Keyword arguments for the package dataclass.
    """
    path = (root_path / str(package_settings.path)).resolve()
    changelog = (root_path / str(package_settings.changelog)).resolve()
    towncrier = (root_path / str(package_settings.towncrier_settings)).resolve()
    raw_code_path = package_settings.get("code_path", "src")
    code_path = (path / str(raw_code_path)).resolve()
    package_name = package_settings.name
    enabled = bool(package_name)
    version = version_func(path) if enabled else ""
    publish = bool(package_settings.get("publish", True))
    default_base_package = t.DEFAULT_BASE_PACKAGES.get(package_type, "")
    base_package = package_settings.get("base_package", default_base_package)
    payload = {
        "enabled": enabled,
        "name": package_name,
        "path": path,
        "code_path": code_path,
        "base_package": base_package,
        "version": version,
        "publish": publish,
        "changelog": changelog,
        "towncrier": towncrier,
        "type": package_type,
        "primary": bool(package_settings.get("primary", False)),
        "section": str(package_settings.get("section", "") or ""),
    }
    return payload


def _get_python_version(package_settings: DynaBox, data: tomlkit.TOMLDocument) -> str:
    default = defaults.PYTHON_VERSION
    versions = package_settings.get("python_version")
    if not versions:
        versions = pyproject_utils.python_versions(data)
        versions = versions[0] if versions else default
    return versions


def _get_python_versions(
    package_settings: DynaBox, data: tomlkit.TOMLDocument
) -> list[str]:
    default = defaults.PYTHON_VERSIONS
    versions = package_settings.get("python_versions")
    if not versions:
        versions = pyproject_utils.python_versions(data) or default
    return versions


def _get_plone_versions(
    package_settings: DynaBox, data: tomlkit.TOMLDocument
) -> list[str]:
    default = defaults.PLONE_VERSIONS
    versions = package_settings.get("plone_versions")
    if not versions:
        versions = pyproject_utils.plone_versions(data) or default
    return versions


def _build_backend_package(
    root_path: Path,
    package_settings: DynaBox,
    package_type: str = "python-plone",
) -> t.BackendPackage:
    """Build a package of the python family from one raw package table.

    :param root_path: Repository root.
    :param package_settings: Raw ``package`` table read from ``repository.toml``.
    :param package_type: Canonical package type.
    :returns: The package.
    """
    version_func = versions.get_backend_version
    package_info = _get_package_info(
        root_path, package_settings, package_type, version_func
    )
    if package_info["enabled"]:
        package_path = package_info["path"]
        version_txt = package_path / "version.txt"
        pyproject_toml = package_path / "pyproject.toml"
        pyproject_data = pyproject_utils.parse_pyproject(pyproject_toml)
        package_info["managed_by_uv"] = pyproject_utils.managed_by_uv(pyproject_toml)
        # Python and Plone versions
        package_info["python_versions"] = _get_python_versions(
            package_settings, pyproject_data
        )
        package_info["python_version"] = _get_python_version(
            package_settings, pyproject_data
        )
        package_info["plone_versions"] = _get_plone_versions(
            package_settings, pyproject_data
        )
        base_package_version = pyproject_utils.current_base_package(
            pyproject_toml,
            package_info["base_package"],
        )
        if not base_package_version and version_txt.exists():
            # Get the version from the `version.txt` file as a fallback
            base_package_version = version_txt.read_text().strip()
        package_info["base_package_version"] = base_package_version
    else:
        package_info["managed_by_uv"] = False
        package_info["python_versions"] = []
        package_info["python_version"] = ""
        package_info["plone_versions"] = []
        package_info["base_package_version"] = ""

    return t.BackendPackage(**package_info)


def get_backend(root_path: Path, raw_settings: Dynaconf) -> t.BackendPackage:
    """Return package information for the backend."""
    return _build_backend_package(root_path, raw_settings.backend.package)


def _build_frontend_package(
    root_path: Path,
    package_settings: DynaBox,
    package_type: str = "node-volto",
) -> t.FrontendPackage:
    """Build a package of the node family from one raw package table.

    :param root_path: Repository root.
    :param package_settings: Raw ``package`` table read from ``repository.toml``.
    :param package_type: Canonical package type.
    :returns: The package.
    """
    version_func = versions.get_frontend_version
    package_info = _get_package_info(
        root_path, package_settings, package_type, version_func
    )
    if package_info["enabled"]:
        path = frontend_root(root_path, package_info["path"])
        package_info["base_package_version"] = frontend_utils.package_version(
            path,
            package_info["base_package"],
        )
        package_info["volto_version"] = frontend_utils.package_version(
            path,
            "@plone/volto",
        )
    else:
        package_info["base_package_version"] = ""
        package_info["volto_version"] = ""

    return t.FrontendPackage(**package_info)


def get_frontend(root_path: Path, raw_settings: Dynaconf) -> t.FrontendPackage:
    """Return package information for the frontend."""
    return _build_frontend_package(root_path, raw_settings.frontend.package)


#: One builder per family. The language prefix of a package type decides how a
#: package is read, so the family is what selects the builder.
PACKAGE_BUILDERS: dict[str, Callable] = {
    t.FAMILY_PYTHON: _build_backend_package,
    t.FAMILY_NODE: _build_frontend_package,
}


def build_package(
    root_path: Path, package_settings: DynaBox, package_type: str
) -> t.Package:
    """Build a package of any type from one raw ``[[package]]`` table.

    :param root_path: Repository root.
    :param package_settings: Raw ``[[package]]`` entry.
    :param package_type: Canonical package type.
    :returns: The package.
    """
    family = t.PACKAGE_FAMILIES[package_type]
    builder = PACKAGE_BUILDERS[family]
    return builder(root_path, package_settings, package_type)
