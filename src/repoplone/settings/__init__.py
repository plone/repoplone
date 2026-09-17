from . import spec
from .parser import parse_config
from dynaconf.base import LazySettings
from pathlib import Path
from repoplone import _types as t
from repoplone import utils
from repoplone.release.config import build_release_steps
from repoplone.utils import _git as git_utils
from repoplone.utils._github import derive_issues_url
from repoplone.utils._path import get_cwd_path
from typing import Any

import warnings


DEPRECATIONS: dict[str, dict] = {
    "repository.managed_by_uv": {
        "path": ("REPOSITORY", "managed_by_uv"),
        "version": "1.0.0",
    },
    "backend.path": {
        "path": ("BACKEND", "path"),
        "version": "1.0.0",
    },
    "frontend.path": {
        "path": ("FRONTEND", "path"),
        "version": "1.0.0",
    },
    "repository.compose": {
        "path": ("REPOSITORY", "compose"),
        "data_type": str,
        "version": "1.0.0",
    },
}


def _check_deprecations(raw_settings: LazySettings) -> list[str]:
    """List deprecations found in repository.toml."""
    deprecations = []
    as_dict: dict = raw_settings.as_dict()
    for key, info in DEPRECATIONS.items():
        value: Any = as_dict
        for item in info["path"]:
            value = value.get(item, None)
            if value is None:
                break
        version = info["version"]
        data_type = info.get("data_type")
        if data_type and isinstance(value, data_type):
            deprecations.append(
                f"Setting {key} as `{data_type.__name__}` is deprecated "
                f"and will be removed in version {version}"
            )
        elif value and not data_type:
            deprecations.append(
                f"Setting {key} is deprecated and will be removed in version {version}"
            )
    return deprecations


def _get_compose_path(root_path: Path, raw_settings: LazySettings) -> list[Path]:
    paths = []
    # A repository need not ship compose files at all -- a plain Python package
    # has none. Declaring [repository] replaces the shipped defaults wholesale,
    # so the key can genuinely be absent rather than falling back to them.
    raw_compose = raw_settings.repository.get("compose", []) or []
    if isinstance(raw_compose, str):
        raw_compose = [raw_compose]
    for compose_file in raw_compose:
        paths.append(root_path / compose_file)
    return paths


def _get_raw_settings(cwd_path: Path) -> tuple[LazySettings, int]:
    raw_settings = parse_config(cwd_path)
    try:
        _ = raw_settings.repository.name
    except AttributeError:
        raise RuntimeError() from None
    spec_version = spec.resolve_spec_version(raw_settings)
    if spec_version == 1:
        # Spec 2 carries no legacy keys: there they are errors, raised while
        # the packages are read, not deprecation warnings.
        for deprecation in _check_deprecations(raw_settings):
            warnings.warn(deprecation, DeprecationWarning, 1)
    return raw_settings, spec_version


def _get_packages(
    root_path: Path, raw_settings: LazySettings, spec_version: int
) -> list[t.Package]:
    """Return every package declared in a file, in document order.

    A spec 1 file declares at most one package per family, so it is normalized
    into the same list: everything downstream then works the same for both
    specs.

    :param root_path: Repository root.
    :param raw_settings: Parsed settings.
    :param spec_version: Spec version the file selected.
    :returns: The enabled packages.
    """
    tables = spec.package_tables(raw_settings, spec_version)
    packages: list[t.Package] = []
    declared_base_package: set[str] = set()
    if spec_version == 1:
        backend = utils.get_backend(root_path, raw_settings)
        frontend = utils.get_frontend(root_path, raw_settings)
        packages = [package for package in (backend, frontend) if package.enabled]
    else:
        for position, table in enumerate(tables):
            package_type = spec.normalize_type(table.get("type", ""), position)
            package = utils.build_package(root_path, table, package_type)
            if table.get("base_package", ""):
                declared_base_package.add(package.name)
            packages.append(package)
    spec.check_packages(packages)
    spec.normalize_primaries(packages)
    for warning in spec.base_package_warnings(packages, declared_base_package):
        warnings.warn(warning, UserWarning, 1)
    return packages


def _family_primary(
    root_path: Path,
    raw_settings: LazySettings,
    packages: list[t.Package],
    family: str,
) -> Any:
    """Return the primary package of a family, or its disabled placeholder.

    ``settings.backend`` and ``settings.frontend`` are read by project release
    hooks and appear in ``settings dump``, so they keep answering for every
    repository -- with the placeholder built from the shipped defaults when a
    family declares no package, exactly as a disabled component does today.

    :param root_path: Repository root.
    :param raw_settings: Parsed settings.
    :param packages: Every package declared in the file.
    :param family: Family name.
    :returns: The family's primary package.
    """
    primary = t.resolve_primary(packages, family)
    if primary is not None:
        return primary
    builder = utils.get_backend if family == t.FAMILY_PYTHON else utils.get_frontend
    return builder(root_path, raw_settings)


def _get_settings(cwd_path: Path) -> t.RepositorySettings:
    """Given a path to a repository root or repository.toml

    return repository settings."""
    raw_settings, spec_version = _get_raw_settings(cwd_path)
    repository = raw_settings.repository
    root_path: Path = repository.__root__
    name: str = repository.name
    container_images_prefix: str = repository.get("container_images_prefix", "") or ""
    root_changelog: Path = root_path / repository.changelog
    version_path: Path = root_path / repository.version
    version: str = version_path.read_text().strip()
    version_format: str = repository.get("version_format", "semver")
    compose_path: list[Path] = _get_compose_path(root_path, raw_settings)
    repository_towncrier: dict = repository.get("towncrier", {})
    packages = _get_packages(root_path, raw_settings, spec_version)
    backend = _family_primary(root_path, raw_settings, packages, t.FAMILY_PYTHON)
    managed_by_uv = backend.managed_by_uv
    frontend = _family_primary(root_path, raw_settings, packages, t.FAMILY_NODE)
    towncrier = utils.get_towncrier_settings(
        root_path, packages, repository_towncrier, spec_version
    )
    changelogs = utils.get_changelogs(root_changelog, backend, frontend)
    remote_origin = git_utils.remote_origin(root_path)
    issues_url: str = repository.get("issues_url", "") or ""
    if not issues_url:
        issues_url = derive_issues_url(remote_origin)
    raw_release = repository.get("release", None)
    if hasattr(raw_release, "to_dict"):
        raw_release = raw_release.to_dict()
    release_steps = build_release_steps(raw_release, spec_version)
    return t.RepositorySettings(
        name=name,
        managed_by_uv=managed_by_uv,
        root_path=root_path,
        version=version,
        version_format=version_format,
        container_images_prefix=container_images_prefix,
        backend=backend,
        frontend=frontend,
        version_path=version_path,
        compose_path=compose_path,
        towncrier=towncrier,
        changelogs=changelogs,
        release_steps=release_steps,
        remote_origin=remote_origin,
        issues_url=issues_url,
        spec_version=spec_version,
        packages=packages,
    )


def get_settings() -> t.RepositorySettings:
    """Return base settings."""
    cwd_path = get_cwd_path()
    return _get_settings(cwd_path)
