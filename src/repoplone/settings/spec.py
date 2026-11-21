"""Resolve the specification version of a ``repository.toml`` and read its packages.

Specification 1 declares one ``[backend.package]`` and one ``[frontend.package]``
table. Specification 2, selected by a top-level ``spec_version = "2"``, replaces
both with a flat ``[[package]]`` array whose entries carry a ``type``.

The JSON Schemas shipped in :mod:`repoplone.schemas` describe the shape of both.
What lives here is everything a schema cannot express: which spec a file
selects, the rules that span several packages, and error messages naming the
offending package.
"""

from dynaconf.base import LazySettings
from repoplone import _types as t
from repoplone.exceptions import RepoPloneException
from typing import Any


SETTINGS_FILE = "repository.toml"

#: Accepted values of ``spec_version``, mapped to the spec they select.
SPEC_VERSIONS: dict[str, int] = {
    "1": 1,
    "1.0": 1,
    "2": 2,
    "2.0": 2,
}

DEFAULT_SPEC_VERSION = 1

#: Spec 1 keys that spec 2 dropped. Reported with the replacement.
LEGACY_KEYS: dict[str, str] = {
    "managed_by_uv": "read from the backend package's pyproject.toml",
    "backend": "replaced by a [[package]] entry with type = 'python-plone'",
    "frontend": "replaced by a [[package]] entry with type = 'node-volto'",
}


class RepositorySpecError(RepoPloneException):
    """Raised when ``repository.toml`` does not match its specification."""


def _fail(message: str) -> None:
    """Raise a spec error naming the file it came from.

    :param message: What is wrong, phrased for the person editing the file.
    :raises RepositorySpecError: Always.
    """
    raise RepositorySpecError(f"{SETTINGS_FILE}: {message}")


def resolve_spec_version(raw_settings: LazySettings) -> int:
    """Return the specification version a file selects.

    A file with no ``spec_version`` is a spec 1 file, which is how every
    ``repository.toml`` written before spec 2 keeps working untouched.

    :param raw_settings: Parsed settings.
    :returns: The spec version.
    :raises RepositorySpecError: If ``spec_version`` is not a supported value.
    """
    raw = raw_settings.get("spec_version", None)
    if raw is None:
        return DEFAULT_SPEC_VERSION
    if not isinstance(raw, str):
        supported = ", ".join(f'"{key}"' for key in SPEC_VERSIONS)
        _fail(
            f"spec_version must be a string, got {raw!r}. "
            f"Quote it, as one of {supported}."
        )
    version = SPEC_VERSIONS.get(str(raw))
    if version is None:
        supported = ", ".join(f'"{key}"' for key in SPEC_VERSIONS)
        _fail(f"spec_version {raw!r} is not supported. Use one of {supported}.")
    return int(version)  # type: ignore[arg-type]


def normalize_type(raw_type: Any, position: int) -> str:
    """Return the canonical name of a package type.

    :param raw_type: Value of the entry's ``type`` key.
    :param position: Index of the entry, used to name it in errors.
    :returns: The canonical type name.
    :raises RepositorySpecError: If the type is missing or unknown.
    """
    if not raw_type:
        known = ", ".join(sorted(t.PACKAGE_FAMILIES))
        _fail(f"[[package]] #{position + 1} has no type. Use one of {known}.")
    name = str(raw_type)
    name = t.PACKAGE_TYPE_ALIASES.get(name, name)
    if name not in t.PACKAGE_FAMILIES:
        known = ", ".join(sorted(t.PACKAGE_FAMILIES))
        _fail(
            f"[[package]] #{position + 1} has an unknown type {raw_type!r}. "
            f"Use one of {known}."
        )
    return name


def _reject_legacy_keys(raw_settings: LazySettings) -> None:
    """Reject spec 1 keys found in a spec 2 file.

    :param raw_settings: Parsed settings.
    :raises RepositorySpecError: If any legacy key is present.
    """
    repository = raw_settings.get("repository", {}) or {}
    if repository.get("managed_by_uv", None) is not None:
        _fail(
            "repository.managed_by_uv is not part of spec 2 "
            f"({LEGACY_KEYS['managed_by_uv']}). Run `repoplone settings migrate`."
        )
    for key in ("backend", "frontend"):
        section = raw_settings.get(key, None)
        if not section:
            continue
        # settings/default.toml always preloads an empty [<key>.package] table,
        # so only a package carrying a name was written by the user.
        package = section.get("package", None) or {}
        if package.get("name", ""):
            _fail(
                f"[{key}.package] is not part of spec 2 "
                f"({LEGACY_KEYS[key]}). Run `repoplone settings migrate`."
            )
        if section.get("path", ""):
            _fail(
                f"[{key}] path is not part of spec 2 "
                f"({LEGACY_KEYS[key]}). Run `repoplone settings migrate`."
            )
    compose = repository.get("compose", None)
    if isinstance(compose, str):
        _fail(
            "repository.compose must be a list in spec 2. "
            "Run `repoplone settings migrate`."
        )


def _raw_tables(raw_settings: LazySettings) -> list:
    """Return the raw ``[[package]]`` entries of a file.

    :param raw_settings: Parsed settings.
    :returns: The entries, possibly empty.
    :raises RepositorySpecError: If ``package`` is not an array of tables.
    """
    raw = raw_settings.get("package", None)
    if raw is None:
        return []
    if isinstance(raw, dict) or not isinstance(raw, list):
        _fail(
            "package must be an array of tables. "
            "Write [[package]], with two brackets, once per package."
        )
    return list(raw)


def package_tables(raw_settings: LazySettings, spec_version: int) -> list:
    """Return the raw package tables of a file, validated against its spec.

    :param raw_settings: Parsed settings.
    :param spec_version: Spec version the file selected.
    :returns: The raw ``[[package]]`` entries; empty for a spec 1 file.
    :raises RepositorySpecError: If the file mixes the two specs.
    """
    tables = _raw_tables(raw_settings)
    if spec_version == 1:
        if tables:
            _fail(
                'a [[package]] array requires spec_version = "2". '
                "Add it, or declare [backend.package] / [frontend.package]."
            )
        return []
    _reject_legacy_keys(raw_settings)
    return tables


def check_packages(packages: list[t.Package]) -> None:
    """Check the rules that span several packages.

    These are the rules JSON Schema cannot express: uniqueness across entries,
    and at most one primary package per family.

    :param packages: The packages read from a spec 2 file.
    :raises RepositorySpecError: If any rule is broken.
    """
    seen_names: set[str] = set()
    seen_paths: set[str] = set()
    for package in packages:
        if package.name in seen_names:
            _fail(f"package {package.name!r} is declared more than once.")
        seen_names.add(package.name)
        path = str(package.path)
        if path in seen_paths:
            _fail(f"more than one package declares the path {path!r}.")
        seen_paths.add(path)

    for family in (t.FAMILY_PYTHON, t.FAMILY_NODE):
        primaries = [
            package.name
            for package in packages
            if package.family == family and package.primary
        ]
        if len(primaries) > 1:
            names = ", ".join(repr(name) for name in primaries)
            _fail(
                f"the {family} family declares more than one primary package "
                f"({names}). Mark exactly one with primary = true."
            )


def normalize_primaries(packages: list[t.Package]) -> None:
    """Mark the resolved primary package of each family, in place.

    A family whose file names no primary still has one -- the first entry in
    document order. Setting the flag makes that explicit, so everything
    downstream, ``settings dump`` included, reads one answer.

    :param packages: The packages read from a spec 2 file.
    """
    for family in (t.FAMILY_PYTHON, t.FAMILY_NODE):
        primary = t.resolve_primary(packages, family)
        if primary is not None:
            primary.primary = True


def base_package_warnings(packages: list[t.Package], declared: set[str]) -> list[str]:
    """Return warnings for base packages declared where they have no effect.

    ``base_package`` is a component-level setting: only the family's primary
    package is consulted for it.

    Every package of an ecosystem type *resolves* a base package, since the
    type carries a default. Only the ones the file names are worth warning
    about, which is what ``declared`` carries.

    :param packages: The packages read from a spec 2 file.
    :param declared: Names of the packages whose table sets ``base_package``.
    :returns: One warning per package that declares a useless base package.
    """
    warnings = []
    for family in (t.FAMILY_PYTHON, t.FAMILY_NODE):
        primary = t.resolve_primary(packages, family)
        if primary is None:
            continue
        for package in packages:
            if package.family != family or package is primary:
                continue
            if package.name in declared:
                warnings.append(
                    f"Package {package.name} sets base_package, which only has "
                    f"an effect on the primary package of the {family} family "
                    f"({primary.name})."
                )
    return warnings
