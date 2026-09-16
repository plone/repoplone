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

# Projects under tests/_resources/<name>/repository.toml are all spec 1.
PROJECT_FILES = sorted(RESOURCES.glob("*/repository.toml"))


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

VALID_SPEC1_FILES = (
    PROJECT_FILES + LEGACY_SPEC1_FILES + _fixtures("spec1", invalid=False)
)
INVALID_SPEC1_FILES = _fixtures("spec1", invalid=True)
VALID_SPEC2_FILES = _fixtures("spec2", invalid=False)
INVALID_SPEC2_FILES = _fixtures("spec2", invalid=True)


def _load(path: Path) -> dict:
    """Parse a TOML file into plain Python types.

    ``unwrap`` matters: jsonschema matches native types, and tomlkit's own
    wrappers do not all subclass them.

    :param path: File to parse.
    :returns: The parsed document.
    """
    return tomlkit.parse(path.read_text()).unwrap()


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


@pytest.mark.parametrize("spec_version", [1, 2])
def test_shipped_schema_matches_pytest_jsonschema(spec_version: int):
    """The schemas here and the ones pytest-jsonschema publishes are the same.

    Both copies exist on purpose: repoplone reads its own at runtime, and
    pytest-jsonschema serves the published one to other projects. This fails
    the moment someone edits one without the other, which is the only way
    they can silently diverge.
    """
    name = schemas.SPEC_SCHEMAS[spec_version]
    assert schemas.load(name) == plugin_schemas.load(name)


@pytest.mark.parametrize("path", VALID_SPEC1_FILES, ids=_ids(VALID_SPEC1_FILES))
def test_valid_spec1_file_through_plugin(schema_validate_file, path: Path):
    """The published schema works through pytest-jsonschema's own code path."""
    assert schema_validate_file(path=path, schema_name="repository-v1") is True


@pytest.mark.parametrize("path", VALID_SPEC2_FILES, ids=_ids(VALID_SPEC2_FILES))
def test_valid_spec2_file_through_plugin(schema_validate_file, path: Path):
    assert schema_validate_file(path=path, schema_name="repository-v2") is True


@pytest.mark.parametrize("path", INVALID_SPEC2_FILES, ids=_ids(INVALID_SPEC2_FILES))
def test_invalid_spec2_file_through_plugin(schema_validate_file, path: Path):
    assert schema_validate_file(path=path, schema_name="repository-v2") is False
