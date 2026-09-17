"""Manage the metadata of a frontend Volto distribution.

A Volto distribution package publishes, alongside its own ``dependencies``, the
exact versions of the add-ons it was built with and a custom ``volto_version``
field pointing at the Volto core release it targets.

This module handles both sides of that contract:

- Producer side (:func:`stamp_volto_version`): when releasing a distribution,
  record the ``@plone/volto`` tag from ``mrs.developer.json`` into the package's
  ``package.json`` ``volto_version`` field, so the published package advertises
  the Volto core it targets.
- Consumer side (:func:`sync_distribution`): when a project built on top of a
  distribution upgrades it, fetch that metadata from the npm registry and write
  it to ``frontend/distribution.json``, which a ``.pnpmfile.cjs`` hook uses to
  enforce those versions across the whole pnpm workspace.
"""

from pathlib import Path
from repoplone import _types as t
from repoplone.utils._path import frontend_root as _resolve_frontend_root
from repoplone.utils._requests import get_remote_data

import json


DISTRIBUTION_FILENAME = "distribution.json"

NPM_REGISTRY = "https://registry.npmjs.org"


def _frontend_root(settings: t.RepositorySettings) -> Path:
    """Return the frontend root path of the primary frontend package."""
    return _resolve_frontend_root(settings.root_path, settings.frontend.path)


def fetch_distribution_metadata(
    package_name: str, version: str
) -> tuple[dict[str, str], str | None]:
    """Return the ``dependencies`` and ``volto_version`` of a distribution.

    Reads the full npm packument for ``package_name`` and extracts the metadata
    published for ``version``.
    """
    url = f"{NPM_REGISTRY}/{package_name}"
    resp = get_remote_data(url)
    data = resp.json()
    releases = data.get("versions", {})
    release = releases.get(version)
    if release is None:
        raise ValueError(
            f"Version {version} of {package_name} not found in the npm registry"
        )
    dependencies: dict[str, str] = release.get("dependencies", {}) or {}
    volto_version: str | None = release.get("volto_version") or None
    return dependencies, volto_version


def stamp_volto_version(settings: t.RepositorySettings, package: t.Package) -> str:
    """Record the Volto core version in the distribution package's package.json.

    Reads the ``@plone/volto`` checkout tag from ``mrs.developer.json`` and writes
    it verbatim to the ``volto_version`` field of the frontend package's
    ``package.json``. This is the producer-side counterpart of
    :func:`sync_distribution`: once published, that field lets consumers detect the
    distribution and enforce its dependencies.

    Returns the stamped version. Raises ``ValueError`` when the core tag is
    missing.

    :param settings: Repository settings.
    :param package: Frontend package to stamp.
    :returns: The stamped Volto version.
    :raises ValueError: If the core tag or the package ``package.json`` is missing.
    """
    from repoplone.utils.dependencies import frontend as frontend_utils

    frontend_root = _resolve_frontend_root(settings.root_path, package.path)
    volto_version = frontend_utils.get_core_tag(frontend_root)
    if not volto_version:
        raise ValueError("Missing mrs.developer.json @plone/volto core tag")
    package_json_path = package.path / "package.json"
    if not package_json_path.exists():
        raise ValueError(f"Missing package.json at {package_json_path}")
    data = json.loads(package_json_path.read_text())
    data["volto_version"] = volto_version
    package_json_path.write_text(f"{json.dumps(data, indent=2, ensure_ascii=False)}\n")
    return volto_version


def write_distribution_file(frontend_root: Path, data: dict) -> Path:
    """Write the distribution enforcement data to ``distribution.json``."""
    path = frontend_root / DISTRIBUTION_FILENAME
    path.write_text(f"{json.dumps(data, indent=2)}\n")
    return path


def sync_distribution(settings: t.RepositorySettings, version: str) -> bool:
    """Refresh the distribution enforcement data for ``version``.

    A Volto distribution is identified by the custom ``volto_version`` field it
    publishes; plain Volto core and non-distribution base packages do not publish
    it. When the base package is a distribution, its enforced ``dependencies`` are
    written to ``distribution.json`` and the ``@plone/volto`` entry in
    ``mrs.developer.json`` is aligned to the distribution's ``volto_version``.

    Returns True when the project is a distribution and the data was synced,
    False when the base package is not a distribution (nothing to enforce).
    """
    from repoplone.utils.dependencies import frontend as frontend_utils

    package_name = settings.frontend.base_package
    dependencies, volto_version = fetch_distribution_metadata(package_name, version)
    if not volto_version:
        # Not a Volto distribution: nothing to enforce.
        return False
    frontend_root = _frontend_root(settings)
    data = {
        "name": package_name,
        "version": version,
        "volto_version": volto_version,
        "dependencies": dependencies,
    }
    write_distribution_file(frontend_root, data)
    frontend_utils.update_core_tag_mrs_developer(frontend_root, volto_version)
    return True
