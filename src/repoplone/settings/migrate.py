"""Rewrite a specification 1 ``repository.toml`` into specification 2.

The rewrite goes through tomlkit rather than a ``tomllib`` load and re-dump, so
comments, key order and formatting survive it. A configuration file is
something a person reads, and losing their comments to a migration is a poor
trade for a slightly simpler implementation.
"""

from pathlib import Path
from repoplone import _types as t
from repoplone.exceptions import RepoPloneException
from repoplone.release.steps import RENAMED_STEPS

import tomlkit


SETTINGS_FILE = "repository.toml"

#: Spec 1 component tables, mapped to the type their package becomes.
COMPONENT_TYPES: dict[str, str] = {
    "backend": "python-plone",
    "frontend": "node-volto",
}

#: Keys spec 2 dropped, as ``(table, key)`` pairs.
DROPPED_KEYS: tuple[tuple[str, str], ...] = (
    ("repository", "managed_by_uv"),
    ("backend", "path"),
    ("frontend", "path"),
)

#: Keys that never belonged on a package table.
DROPPED_PACKAGE_KEYS: tuple[str, ...] = ("enabled",)


class MigrationError(RepoPloneException):
    """Raised when a ``repository.toml`` cannot be migrated."""


def _package_entries(document: tomlkit.TOMLDocument) -> list[tomlkit.items.Table]:
    """Return the ``[[package]]`` entries a spec 1 document becomes.

    :param document: Parsed ``repository.toml``.
    :returns: One table per component that declares a named package.
    """
    entries = []
    for component, package_type in COMPONENT_TYPES.items():
        section = document.get(component, None)
        if section is None:
            continue
        package = section.get("package", None)
        if package is None or not package.get("name", ""):
            continue
        entry = tomlkit.table()
        entry["type"] = package_type
        entry["primary"] = True
        for key, value in package.items():
            if key in DROPPED_PACKAGE_KEYS:
                continue
            entry[key] = value
        entries.append(entry)
    return entries


def _normalize_compose(document: tomlkit.TOMLDocument) -> bool:
    """Turn a bare ``compose`` string into a list.

    :param document: Parsed ``repository.toml``.
    :returns: Whether anything changed.
    """
    repository = document.get("repository", None)
    if repository is None:
        return False
    compose = repository.get("compose", None)
    if not isinstance(compose, str):
        return False
    repository["compose"] = [compose]
    return True


def _rename_steps(document: tomlkit.TOMLDocument) -> list[str]:
    """Rewrite release step ids that spec 2 renamed.

    :param document: Parsed ``repository.toml``.
    :returns: One note per rewrite.
    """
    notes: list[str] = []
    repository = document.get("repository", None)
    if repository is None:
        return notes
    release = repository.get("release", None)
    if release is None:
        return notes
    steps = release.get("steps", None)
    if steps is not None:
        renamed = [RENAMED_STEPS.get(step, step) for step in steps]
        if renamed != list(steps):
            release["steps"] = renamed
            notes.append(
                "Renamed release steps: "
                + ", ".join(
                    f"{old} -> {new}"
                    for old, new in RENAMED_STEPS.items()
                    if old in steps
                )
            )
    registry = release.get("registry", None)
    for entry_id, entry in (registry or {}).items():
        function_id = entry.get("function", "")
        replacement = RENAMED_STEPS.get(function_id)
        if replacement:
            entry["function"] = replacement
            notes.append(
                f"[repository.release.registry.{entry_id}].function: "
                f"{function_id} -> {replacement}"
            )
    return notes


def _drop_legacy_keys(document: tomlkit.TOMLDocument) -> list[str]:
    """Remove the keys spec 2 dropped.

    :param document: Parsed ``repository.toml``.
    :returns: One note per removal.
    """
    notes = []
    for table_name, key in DROPPED_KEYS:
        table = document.get(table_name, None)
        if table is not None and key in table:
            del table[key]
            notes.append(f"Removed deprecated {table_name}.{key}")
    return notes


def _innermost_table(table: tomlkit.items.Table) -> tomlkit.items.Table:
    """Return the last sub-table of a table, recursively.

    Trailing trivia nests with the tables: a comment after
    ``[frontend.package]`` lives inside *that* table, not inside
    ``[frontend]``.

    :param table: Table to descend from.
    :returns: The deepest last sub-table, or the table itself.
    """
    for key, item in reversed(table.value.body):
        if key is not None and isinstance(item, tomlkit.items.Table):
            return _innermost_table(item)
        if key is not None:
            break
    return table


def _trailing_comments(table: tomlkit.items.Table) -> list[str]:
    """Return the comments written after a table's last key.

    In TOML everything after a table header belongs to that table until the
    next one, so a comment introducing the *following* table is stored inside
    the preceding one and disappears with it. tomlkit offers no way to move an
    unkeyed item to a chosen position in a document, and appending it puts the
    comment below whatever it was introducing -- worse than losing it. So the
    comments are reported instead, for the author to put back where they meant.

    :param table: Table about to be removed.
    :returns: The comment lines, in order.
    """
    return [
        item.as_string().strip()
        for key, item in _innermost_table(table).value.body
        if key is None and isinstance(item, tomlkit.items.Comment)
    ]


def _remove_components(document: tomlkit.TOMLDocument) -> list[str]:
    """Drop the spec 1 component tables.

    :param document: Parsed ``repository.toml``.
    :returns: A note for each comment the removal takes with it.
    """
    notes = []
    for component in COMPONENT_TYPES:
        table = document.get(component, None)
        if table is None:
            continue
        for comment in _trailing_comments(table):
            notes.append(f"Dropped a comment that followed [{component}]: {comment}")
        del document[component]
    return notes


def migrate_document(document: tomlkit.TOMLDocument) -> list[str]:
    """Rewrite a parsed spec 1 document into spec 2, in place.

    :param document: Parsed ``repository.toml``.
    :returns: Notes describing what changed, for the caller to report.
    :raises MigrationError: If the document already declares a spec version.
    """
    if "spec_version" in document:
        raise MigrationError(
            f"{SETTINGS_FILE} already declares "
            f"spec_version = {document['spec_version']!r}; nothing to migrate."
        )
    notes: list[str] = []
    entries = _package_entries(document)
    notes.extend(_drop_legacy_keys(document))
    if _normalize_compose(document):
        notes.append("Turned repository.compose into a list")
    notes.extend(_rename_steps(document))

    notes.extend(_remove_components(document))

    packages = tomlkit.aot()
    for entry in entries:
        packages.append(entry)
    document["package"] = packages

    for entry in entries:
        notes.append(f'Declared {entry["name"]} as type = "{entry["type"]}"')
    return notes


def dump_migrated(document: tomlkit.TOMLDocument) -> str:
    """Serialize a migrated document, with ``spec_version`` first.

    The key describes the file rather than the repository, so it belongs
    before the first table. tomlkit has no public way to insert at the top of
    a document, and rebuilding the body to do so would risk the comments this
    whole module exists to preserve -- so the line is prepended to the dump.

    :param document: Migrated ``repository.toml``.
    :returns: The file text.
    """
    return f'spec_version = "2"\n\n{tomlkit.dumps(document)}'


def changelog_heading_note(document: tomlkit.TOMLDocument) -> str:
    """Return the warning about changelog headings changing, if it applies.

    Migrating is the deliberate moment section titles become package names.
    Writing ``section`` keys to preserve the old headings would pin spec 1
    behaviour into every migrated file, so the change is reported instead.

    :param document: Migrated ``repository.toml``.
    :returns: The note, or an empty string when no package would change.
    """
    names = [
        str(entry["name"])
        for entry in document.get("package", [])
        if not entry.get("section", "")
    ]
    if not names:
        return ""
    listed = ", ".join(names)
    return (
        f"Changelog sections will now be titled {listed}, rather than "
        f'Backend / Frontend. Add `section = "Backend"` to a package to keep '
        f"the old heading."
    )


def migrate_file(path: Path) -> tuple[str, list[str]]:
    """Return the spec 2 rewrite of a ``repository.toml``, without writing it.

    :param path: File to migrate.
    :returns: The migrated text, and notes describing what changed.
    :raises MigrationError: If the file is missing or already spec 2.
    """
    if not path.exists():
        raise MigrationError(f"No {SETTINGS_FILE} found at {path}.")
    document = tomlkit.parse(path.read_text())
    notes = migrate_document(document)
    note = changelog_heading_note(document)
    if note:
        notes.append(note)
    return dump_migrated(document), notes


def validate_migrated(text: str) -> None:
    """Check a migrated document against the spec 2 JSON Schema.

    :param text: The migrated ``repository.toml``.
    :raises MigrationError: If the result does not match the schema.
    """
    try:
        import jsonschema
    except ImportError:  # pragma: no cover - jsonschema is a test dependency
        return
    from repoplone import schemas

    data = tomlkit.parse(text).unwrap()
    schema = schemas.load_for_spec(2)
    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as exc:
        raise MigrationError(
            f"The migrated {SETTINGS_FILE} does not match specification 2: "
            f"{exc.message}"
        ) from exc


def package_types() -> list[str]:
    """Return the canonical package types, for help text.

    :returns: The type names, sorted.
    """
    return sorted(t.PACKAGE_FAMILIES)
