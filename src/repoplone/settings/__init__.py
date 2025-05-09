from .parser import parse_config
from dynaconf.base import LazySettings
from pathlib import Path
from repoplone import _types as t
from repoplone import utils
from repoplone.utils import _git as git_utils
from repoplone.utils._path import get_root_path

import warnings


DEPRECATIONS = {
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
}


def _check_deprecations(raw_settings: LazySettings) -> list[str]:
    """List deprecations found in repository.toml."""
    deprecations = []
    as_dict: dict = raw_settings.as_dict()
    for key, info in DEPRECATIONS.items():
        value = as_dict
        for item in info["path"]:
            value = value.get(item, None)
            if value is None:
                break
        if value:
            version = info["version"]
            deprecations.append(
                f"Setting {key} is deprecated and will be removed in version {version}"
            )
    return deprecations


def _get_raw_settings(root_path: Path) -> LazySettings:
    raw_settings = parse_config()
    try:
        _ = raw_settings.repository.name
    except AttributeError:
        raise RuntimeError() from None
    for deprecation in _check_deprecations(raw_settings):
        warnings.warn(deprecation, DeprecationWarning, 1)
    return raw_settings


def get_settings() -> t.RepositorySettings:
    """Return base settings."""
    root_path = get_root_path()
    raw_settings = _get_raw_settings(root_path)
    name = raw_settings.repository.name
    root_changelog = root_path / raw_settings.repository.changelog
    version_path = root_path / raw_settings.repository.version
    version = version_path.read_text().strip()
    version_format = raw_settings.repository.get("version_format", "semver")
    compose_path = root_path / raw_settings.repository.compose
    repository_towncrier = raw_settings.repository.get("towncrier", {})
    backend = utils.get_backend(root_path, raw_settings)
    managed_by_uv = backend.managed_by_uv
    frontend = utils.get_frontend(root_path, raw_settings)
    towncrier = utils.get_towncrier_settings(backend, frontend, repository_towncrier)
    changelogs = utils.get_changelogs(root_changelog, backend, frontend)
    remote_origin = git_utils.remote_origin(root_path)
    return t.RepositorySettings(
        name=name,
        managed_by_uv=managed_by_uv,
        root_path=root_path,
        version=version,
        version_format=version_format,
        backend=backend,
        frontend=frontend,
        version_path=version_path,
        compose_path=compose_path,
        towncrier=towncrier,
        changelogs=changelogs,
        remote_origin=remote_origin,
    )
