"""Validate ``repository.toml`` files against the JSON Schemas shipped with repoplone.

The schemas gate the shape of a ``repository.toml``. Rules JSON Schema cannot
express -- duplicate package names, one primary package per family, paths
existing on disk -- are checked while the settings are loaded, not here.

Fixtures live in ``tests/_resources/repository_toml/``. A file whose name
carries ``invalid`` must be rejected by its spec's schema; every other file
must be accepted. Adding a fixture is therefore enough to cover it.
"""

from pathlib import Path
from pytest_jsonschema import schemas as plugin_schemas
from repoplone import schemas

import jsonschema
import pytest
import tomlkit


RESOURCES = Path(__file__).parent / "_resources"
REPOSITORY_TOML = RESOURCES / "repository_toml"

PROJECT_FILES = sorted(RESOURCES.glob("*/repository.toml"))


def _load(path: Path) -> dict:
    """Parse a TOML file into plain Python types.

    ``unwrap`` matters: jsonschema matches native types, and tomlkit's own
    wrappers do not all subclass them.

    :param path: File to parse.
    :returns: The parsed document.
    """
    return tomlkit.parse(path.read_text()).unwrap()


def _fixtures(prefix: str, *, invalid: bool) -> list[Path]:
    """Return the fixtures of a spec, split by whether they must be rejected.

    :param prefix: Fixture name prefix, ``spec1`` or ``spec2``.
    :param invalid: Whether to return the fixtures that must fail validation.
    :returns: Matching paths, sorted by name.
    """
    paths = sorted(REPOSITORY_TOML.glob(f"{prefix}_*.toml"))
    return [path for path in paths if ("invalid" in path.name) is invalid]


# Fixtures predating the spec_version key, named without a spec1_ prefix.
LEGACY_SPEC1_FILES = sorted(
    path
    for path in REPOSITORY_TOML.glob("*.toml")
    if not path.name.startswith(("spec1_", "spec2_"))
)


def _declared_spec(path: Path) -> int:
    """Return the spec version a fixture project selects.

    Project fixtures are real repositories of both specs, so the schema to
    validate them against comes from the file itself.

    :param path: Fixture path.
    :returns: ``2`` when the file declares spec 2, ``1`` otherwise.
    """
    return 2 if str(_load(path).get("spec_version", "1")).startswith("2") else 1


SPEC1_PROJECT_FILES = [p for p in PROJECT_FILES if _declared_spec(p) == 1]
SPEC2_PROJECT_FILES = [p for p in PROJECT_FILES if _declared_spec(p) == 2]

VALID_SPEC1_FILES = (
    SPEC1_PROJECT_FILES + LEGACY_SPEC1_FILES + _fixtures("spec1", invalid=False)
)
INVALID_SPEC1_FILES = _fixtures("spec1", invalid=True)
VALID_SPEC2_FILES = SPEC2_PROJECT_FILES + _fixtures("spec2", invalid=False)
INVALID_SPEC2_FILES = _fixtures("spec2", invalid=True)


def _validator(spec_version: int) -> jsonschema.protocols.Validator:
    """Return a validator for a spec version's schema.

    :param spec_version: Spec version, ``1`` or ``2``.
    :returns: A validator bound to that schema.
    """
    schema = schemas.load_for_spec(spec_version)
    cls = jsonschema.validators.validator_for(schema)
    return cls(schema)


def _ids(paths: list[Path]) -> list[str]:
    """Return readable parametrize ids for a list of fixture paths.

    :param paths: Fixture paths.
    :returns: One id per path.
    """
    return [f"{path.parent.name}/{path.name}" for path in paths]


#: Fixtures the *published* spec 2 schema still rejects, because
#: pytest-jsonschema 1.1.0 predates a change made here. Each is expected to
#: fail through the plugin until a release carries the change; strict xfail
#: then turns the fix into a failing test, so the marker cannot be forgotten.
PENDING_UPSTREAM: dict[str, str] = {
    "spec2_node_aurora_default_base_package.toml": (
        "the published schema still requires base_package for node-aurora"
    ),
}


def _plugin_params(paths: list[Path]) -> list:
    """Return parametrize entries, marking the ones the published schema rejects.

    :param paths: Fixture paths.
    :returns: One entry per path, xfailed where upstream lags.
    """
    params = []
    for path in paths:
        reason = PENDING_UPSTREAM.get(path.name)
        marks = [pytest.mark.xfail(strict=True, reason=reason)] if reason else []
        params.append(
            pytest.param(path, marks=marks, id=f"{path.parent.name}/{path.name}")
        )
    return params


@pytest.mark.parametrize("spec_version", [1, 2])
def test_schema_is_valid(spec_version: int):
    """Each shipped schema is itself a valid JSON Schema."""
    schema = schemas.load_for_spec(spec_version)
    cls = jsonschema.validators.validator_for(schema)
    cls.check_schema(schema)


def test_every_resource_repository_toml_is_covered():
    """No fixture is silently left out of the parametrized sets."""
    covered = {
        path
        for group in (
            VALID_SPEC1_FILES,
            INVALID_SPEC1_FILES,
            VALID_SPEC2_FILES,
            INVALID_SPEC2_FILES,
        )
        for path in group
    }
    found = set(PROJECT_FILES) | set(REPOSITORY_TOML.glob("*.toml"))
    assert found == covered


@pytest.mark.parametrize("path", VALID_SPEC1_FILES, ids=_ids(VALID_SPEC1_FILES))
def test_valid_spec1_file(path: Path):
    _validator(1).validate(_load(path))


@pytest.mark.parametrize("path", INVALID_SPEC1_FILES, ids=_ids(INVALID_SPEC1_FILES))
def test_invalid_spec1_file(path: Path):
    with pytest.raises(jsonschema.ValidationError):
        _validator(1).validate(_load(path))


@pytest.mark.parametrize("path", VALID_SPEC2_FILES, ids=_ids(VALID_SPEC2_FILES))
def test_valid_spec2_file(path: Path):
    _validator(2).validate(_load(path))


@pytest.mark.parametrize("path", INVALID_SPEC2_FILES, ids=_ids(INVALID_SPEC2_FILES))
def test_invalid_spec2_file(path: Path):
    with pytest.raises(jsonschema.ValidationError):
        _validator(2).validate(_load(path))


@pytest.mark.parametrize("path", VALID_SPEC1_FILES, ids=_ids(VALID_SPEC1_FILES))
def test_spec1_file_is_not_valid_spec2(path: Path):
    """A spec 1 file never passes as spec 2: it lacks spec_version."""
    with pytest.raises(jsonschema.ValidationError):
        _validator(2).validate(_load(path))


@pytest.mark.parametrize("path", VALID_SPEC2_FILES, ids=_ids(VALID_SPEC2_FILES))
def test_spec2_file_is_not_valid_spec1(path: Path):
    """A spec 2 file never passes as spec 1: spec_version is out of range."""
    with pytest.raises(jsonschema.ValidationError):
        _validator(1).validate(_load(path))


def test_unknown_top_level_table_is_allowed():
    """cookieplone writes a [cookieplone] table that repoplone never reads."""
    for spec_version, name in ((1, "spec1_cookieplone"), (2, "spec2_cookieplone")):
        data = _load(REPOSITORY_TOML / f"{name}.toml")
        assert "cookieplone" in data
        _validator(spec_version).validate(data)


def test_load_unknown_schema_raises():
    with pytest.raises(FileNotFoundError):
        schemas.load("repository-v99")


def test_load_for_unknown_spec_raises():
    with pytest.raises(KeyError):
        schemas.load_for_spec(99)


def test_shipped_spec1_schema_matches_pytest_jsonschema():
    """The schemas here and the ones pytest-jsonschema publishes are the same.

    Both copies exist on purpose: repoplone reads its own at runtime, and
    pytest-jsonschema serves the published one to other projects. This fails
    the moment someone edits one without the other, which is the only way
    they can silently diverge.
    """
    name = schemas.SPEC_SCHEMAS[1]
    assert schemas.load(name) == plugin_schemas.load(name)


@pytest.mark.xfail(
    strict=True,
    reason=(
        "repository-v2 dropped the node-aurora base_package requirement once "
        "the default (@plone/aurora) was settled. pytest-jsonschema 1.1.0 "
        "still ships the stricter copy. When a release carries the change "
        "this XPASSes and fails strictly -- remove the marker then."
    ),
)
def test_shipped_spec2_schema_matches_pytest_jsonschema():
    name = schemas.SPEC_SCHEMAS[2]
    assert schemas.load(name) == plugin_schemas.load(name)


def test_spec2_schemas_differ_only_in_the_known_way():
    """Pin exactly how the two spec 2 copies differ, so nothing else drifts.

    The plain equality check above is expected to fail until pytest-jsonschema
    ships the update; without this, any *other* edit to one copy would hide
    behind that expected failure.
    """
    ours = schemas.load(schemas.SPEC_SCHEMAS[2])
    theirs = plugin_schemas.load(schemas.SPEC_SCHEMAS[2])
    ours_branches = ours["$defs"]["package"]["allOf"]
    theirs_branches = theirs["$defs"]["package"]["allOf"]
    aurora = {
        "$comment": (
            "node-aurora has no built-in base package default, so it must be declared."
        ),
        "if": {
            "required": ["type"],
            "properties": {"type": {"const": "node-aurora"}},
        },
        "then": {"required": ["base_package"]},
    }
    assert theirs_branches == [*ours_branches, aurora]

    # Everything outside that one branch is identical.
    ours_rest = {k: v for k, v in ours.items() if k != "$defs"}
    theirs_rest = {k: v for k, v in theirs.items() if k != "$defs"}
    assert ours_rest == theirs_rest
    ours_defs = {k: v for k, v in ours["$defs"].items() if k != "package"}
    theirs_defs = {k: v for k, v in theirs["$defs"].items() if k != "package"}
    assert ours_defs == theirs_defs


@pytest.mark.parametrize("path", VALID_SPEC1_FILES, ids=_ids(VALID_SPEC1_FILES))
def test_valid_spec1_file_through_plugin(schema_validate_file, path: Path):
    """The published schema works through pytest-jsonschema's own code path."""
    assert schema_validate_file(path=path, schema_name="repository-v1") is True


@pytest.mark.parametrize("path", _plugin_params(VALID_SPEC2_FILES))
def test_valid_spec2_file_through_plugin(schema_validate_file, path: Path):
    assert schema_validate_file(path=path, schema_name="repository-v2") is True


@pytest.mark.parametrize("path", INVALID_SPEC2_FILES, ids=_ids(INVALID_SPEC2_FILES))
def test_invalid_spec2_file_through_plugin(schema_validate_file, path: Path):
    assert schema_validate_file(path=path, schema_name="repository-v2") is False
