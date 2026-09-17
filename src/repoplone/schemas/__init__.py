"""JSON Schemas describing the ``repository.toml`` file format.

The schemas gate the *shape* of a ``repository.toml``: which tables and keys
exist, their types, and which keys each spec version allows. Rules that JSON
Schema cannot express -- duplicate package names, one primary package per
family, paths existing on disk -- are enforced while the settings are loaded.

These files are also meant to be contributed to `pytest-jsonschema
<https://github.com/collective/pytest-jsonschema>`_, which loads a schema by
its file name.
"""

from pathlib import Path

import json


SCHEMAS_PATH = Path(__file__).parent

SPEC_SCHEMAS: dict[int, str] = {
    1: "repository-v1",
    2: "repository-v2",
}


def load(name: str) -> dict:
    """Load a JSON Schema shipped with repoplone.

    :param name: Schema name, without the ``.json`` extension.
    :returns: The parsed schema.
    :raises FileNotFoundError: If no schema with that name is shipped.
    """
    path = SCHEMAS_PATH / f"{name}.json"
    return json.loads(path.read_text())


def load_for_spec(spec_version: int) -> dict:
    """Load the schema describing a given ``repository.toml`` spec version.

    :param spec_version: Spec version, ``1`` or ``2``.
    :returns: The parsed schema.
    :raises KeyError: If the spec version has no schema.
    """
    return load(SPEC_SCHEMAS[spec_version])
