"""Cover the specification rules that JSON Schema cannot express.

The schemas in :mod:`repoplone.schemas` gate the shape of a file. What is
checked here is everything that needs the whole document, or a message naming
the offending package.
"""

from pathlib import Path
from repoplone import _types as t
from repoplone import settings
from repoplone.settings import spec

import pytest


@pytest.fixture
def load(repository_toml_factory, bust_path_cache):
    """Return a callable loading settings from a ``repository_toml`` fixture.

    The fixture files are ``repository.toml`` on their own, so the few files
    every repository has -- the version and the changelog -- are written
    alongside them. Neither carries anything these tests assert on.
    """

    def func(filename: str):
        path = repository_toml_factory(f"repository_toml/{filename}")
        (path / "version.txt").write_text("1.0.0a0\n")
        (path / "CHANGELOG.md").write_text(
            "# Changelog\n\n<!-- towncrier release notes start -->\n"
        )
        return settings._get_settings(path)

    return func


@pytest.mark.parametrize(
    "raw,expected",
    [
        [None, 1],
        ["1", 1],
        ["1.0", 1],
        ["2", 2],
        ["2.0", 2],
    ],
)
def test_resolve_spec_version(raw, expected: int):
    raw_settings = {"spec_version": raw} if raw is not None else {}
    assert spec.resolve_spec_version(raw_settings) == expected  # type: ignore[arg-type]


@pytest.mark.parametrize("raw", ["3", "0", "two", ""])
def test_resolve_spec_version_unsupported(raw: str):
    with pytest.raises(spec.RepositorySpecError, match="not supported"):
        spec.resolve_spec_version({"spec_version": raw})  # type: ignore[arg-type]


def test_resolve_spec_version_must_be_a_string():
    """TOML makes an unquoted 2 an integer, which is the easy mistake."""
    with pytest.raises(spec.RepositorySpecError, match="must be a string"):
        spec.resolve_spec_version({"spec_version": 2})  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "raw,expected",
    [
        ["python-plone", "python-plone"],
        ["python", "python"],
        ["node-volto", "node-volto"],
        ["node-aurora", "node-aurora"],
        ["node", "node"],
        # Deprecated aliases, accepted when reading.
        ["backend", "python-plone"],
        ["frontend", "node-volto"],
    ],
)
def test_normalize_type(raw: str, expected: str):
    assert spec.normalize_type(raw, 0) == expected


def test_normalize_type_missing():
    with pytest.raises(spec.RepositorySpecError, match="has no type"):
        spec.normalize_type("", 0)


def test_normalize_type_unknown():
    with pytest.raises(spec.RepositorySpecError, match="unknown type"):
        spec.normalize_type("ruby", 2)


def test_normalize_type_error_names_the_entry():
    """Positions are 1-based, because nobody counts tables from zero."""
    with pytest.raises(spec.RepositorySpecError, match=r"\[\[package\]\] #3"):
        spec.normalize_type("ruby", 2)


@pytest.mark.parametrize(
    "package_type,family",
    [
        ["python-plone", t.FAMILY_PYTHON],
        ["python", t.FAMILY_PYTHON],
        ["node-volto", t.FAMILY_NODE],
        ["node-aurora", t.FAMILY_NODE],
        ["node", t.FAMILY_NODE],
    ],
)
def test_family_of_each_type(package_type: str, family: str):
    package = t.Package(
        enabled=True,
        name="acme",
        path=Path("/repo"),
        changelog=Path("/repo/CHANGELOG.md"),
        towncrier=Path("/repo/pyproject.toml"),
        base_package="",
        code_path=Path("/repo/src"),
        type=package_type,
    )
    assert package.family == family


def _package(name: str, package_type: str, primary: bool = False) -> t.Package:
    return t.Package(
        enabled=True,
        name=name,
        path=Path("/repo") / name,
        changelog=Path("/repo/CHANGELOG.md"),
        towncrier=Path("/repo/pyproject.toml"),
        base_package="",
        code_path=Path("/repo/src"),
        type=package_type,
        primary=primary,
    )


def test_duplicate_name_is_rejected():
    packages = [_package("acme", "python-plone"), _package("acme", "python")]
    # Same name, different paths: the name is what collides.
    packages[1].path = Path("/repo/other")
    with pytest.raises(spec.RepositorySpecError, match="declared more than once"):
        spec.check_packages(packages)


def test_duplicate_path_is_rejected():
    packages = [_package("one", "python-plone"), _package("two", "python")]
    packages[1].path = packages[0].path
    with pytest.raises(spec.RepositorySpecError, match="declares the path"):
        spec.check_packages(packages)


def test_two_primaries_in_one_family_is_rejected():
    packages = [
        _package("one", "python-plone", primary=True),
        _package("two", "python", primary=True),
    ]
    with pytest.raises(spec.RepositorySpecError, match="more than one primary"):
        spec.check_packages(packages)


def test_one_primary_per_family_is_allowed():
    """A primary python package and a primary node package do not collide."""
    packages = [
        _package("one", "python-plone", primary=True),
        _package("two", "node-volto", primary=True),
    ]
    spec.check_packages(packages)


def test_primary_defaults_to_document_order():
    packages = [_package("one", "python-plone"), _package("two", "python")]
    spec.normalize_primaries(packages)
    assert packages[0].primary is True
    assert packages[1].primary is False


def test_explicit_primary_wins_over_order():
    packages = [
        _package("one", "python-plone"),
        _package("two", "python", primary=True),
    ]
    spec.normalize_primaries(packages)
    assert packages[0].primary is False
    assert packages[1].primary is True


def test_base_package_warning_only_for_declared_values():
    packages = [
        _package("one", "python-plone", primary=True),
        _package("two", "python"),
    ]
    assert spec.base_package_warnings(packages, set()) == []
    warnings = spec.base_package_warnings(packages, {"two"})
    assert len(warnings) == 1
    assert "two" in warnings[0]
    assert "one" in warnings[0]


def test_base_package_on_the_primary_is_never_a_warning():
    packages = [_package("one", "python-plone", primary=True)]
    assert spec.base_package_warnings(packages, {"one"}) == []


# --- Whole-file behaviour -------------------------------------------------


def test_spec1_file_reports_spec_version_1(test_public_project, bust_path_cache):
    assert settings.get_settings().spec_version == 1


def test_spec1_packages_are_normalized_into_the_list(
    test_public_project, bust_path_cache
):
    """Spec 1 files fill `packages` too, so both specs behave the same."""
    result = settings.get_settings()
    assert [package.type for package in result.packages] == [
        "python-plone",
        "node-volto",
    ]
    assert result.backend is result.packages[0]
    assert result.frontend is result.packages[1]


def test_spec1_disabled_component_is_absent_from_packages(
    test_backend_only_no_section_project, bust_path_cache
):
    result = settings.get_settings()
    assert [package.type for package in result.packages] == ["python-plone"]
    assert result.frontend.enabled is False
    assert result.packages_for(t.FAMILY_NODE) == []


def test_flat_array_requires_spec_2(load):
    with pytest.raises(spec.RepositorySpecError, match='requires spec_version = "2"'):
        load("spec1_invalid_flat_package.toml")


def test_component_tables_are_rejected_in_spec_2(load):
    with pytest.raises(spec.RepositorySpecError, match=r"\[backend.package\]"):
        load("spec2_invalid_component_tables.toml")


def test_legacy_key_is_rejected_in_spec_2(load):
    with pytest.raises(spec.RepositorySpecError, match="managed_by_uv"):
        load("spec2_invalid_legacy_key.toml")


def test_compose_string_is_rejected_in_spec_2(load):
    with pytest.raises(spec.RepositorySpecError, match="must be a list"):
        load("spec2_invalid_compose_string.toml")


def test_spec_2_errors_point_at_the_migrate_command(load):
    with pytest.raises(spec.RepositorySpecError, match="settings migrate"):
        load("spec2_invalid_legacy_key.toml")


def test_spec_2_without_packages_is_valid(load):
    result = load("spec2_no_packages.toml")
    assert result.spec_version == 2
    assert result.packages == []
    assert result.backend.enabled is False
    assert result.frontend.enabled is False


# --- Multi-package project ------------------------------------------------


def test_multi_package_project(test_multi_package_project, bust_path_cache):
    result = settings.get_settings()
    assert result.spec_version == 2
    assert [package.name for package in result.packages] == [
        "acme.core",
        "acme.theme",
        "@acme/volto-core",
        "@acme/volto-theme",
    ]


def test_multi_package_families(test_multi_package_project, bust_path_cache):
    result = settings.get_settings()
    assert [p.name for p in result.packages_for(t.FAMILY_PYTHON)] == [
        "acme.core",
        "acme.theme",
    ]
    assert [p.name for p in result.packages_for(t.FAMILY_NODE)] == [
        "@acme/volto-core",
        "@acme/volto-theme",
    ]


def test_multi_package_aliases_point_at_the_primary(
    test_multi_package_project, bust_path_cache
):
    """settings.backend / .frontend are the same objects, not copies."""
    result = settings.get_settings()
    assert result.backend is result.packages[0]
    assert result.frontend is result.packages[2]
    assert isinstance(result.backend, t.BackendPackage)
    assert isinstance(result.frontend, t.FrontendPackage)


def test_multi_package_base_package_defaults(
    test_multi_package_project, bust_path_cache
):
    result = settings.get_settings()
    assert result.backend.base_package == "Products.CMFPlone"
    assert result.frontend.base_package == "@plone/volto"


def test_multi_package_sanity(test_multi_package_project, bust_path_cache):
    assert settings.get_settings().sanity() is True


# --- Root-level package project -------------------------------------------


def test_root_package_project(test_root_package_project, bust_path_cache):
    """The shape #87 needs: one Python package at the repository root."""
    result = settings.get_settings()
    package = result.packages[0]
    assert result.spec_version == 2
    assert package.type == "python"
    assert package.path == result.root_path
    assert package.primary is True


def test_root_package_has_no_node_family(test_root_package_project, bust_path_cache):
    result = settings.get_settings()
    assert result.packages_for(t.FAMILY_NODE) == []
    assert result.frontend.enabled is False


def test_generic_python_has_no_base_package(test_root_package_project, bust_path_cache):
    """A generic package builds on no ecosystem, so it defaults to nothing."""
    result = settings.get_settings()
    assert result.packages[0].base_package == ""


def test_root_package_without_compose(test_root_package_project, bust_path_cache):
    """A plain Python repository ships no compose files."""
    result = settings.get_settings()
    assert result.compose_path == []
    assert result.sanity() is True
