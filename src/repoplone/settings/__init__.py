from .parser import parse_config
from repoplone import _types as t
from repoplone import utils
from repoplone.utils import _git as git_utils
from repoplone.utils._path import get_root_path


def get_settings() -> t.RepositorySettings:
    """Return base settings."""
    root_path = get_root_path()
    raw_settings = parse_config()
    try:
        name = raw_settings.repository.name
    except AttributeError:
        raise RuntimeError() from None
    managed_by_uv = bool(raw_settings.repository.get("managed_by_uv", False))
    root_changelog = root_path / raw_settings.repository.changelog
    version_path = root_path / raw_settings.repository.version
    version = version_path.read_text().strip()
    version_format = raw_settings.repository.get("version_format", "semver")
    compose_path = root_path / raw_settings.repository.compose
    repository_towncrier = raw_settings.repository.get("towncrier", {})
    backend = utils.get_backend(root_path, raw_settings)
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
