from pathlib import Path
from repoplone import _types as t
from repoplone.utils.dependencies import constraints as const_utils

import pytest
import tomlkit


@pytest.fixture
def pyproject_path(test_public_project) -> Path:
    return test_public_project / "backend" / "pyproject.toml"


@pytest.fixture
def pyproject_toml(pyproject_path) -> tomlkit.TOMLDocument:
    return tomlkit.parse(pyproject_path.read_text())


@pytest.fixture
def existing_pins(pyproject_toml) -> t.Requirements:
    from repoplone.utils.dependencies import pyproject as utils

    return utils.get_all_pinned_dependencies(pyproject_toml)


@pytest.mark.parametrize(
    "core_package,core_package_version,constraint,is_present",
    [
        # Package being upgraded — kept (filtered out of existing_pins)
        ["Products.CMFPlone", "6.1.0", "Products.CMFPlone==6.1.0", True],
        # Already pinned in dependency-groups locally — excluded
        ["Products.CMFPlone", "6.1.0", "pytest-plone>=1.0.0a1", False],
        # Upstream-pinned, not locally pinned — kept
        [
            "kitconcept.intranet",
            "1.0.0a17",
            "kitconcept.voltolighttheme==6.0.0a21",
            True,
        ],
        # Already pinned in dependency-groups locally — excluded
        ["kitconcept.intranet", "1.0.0a17", "pytest-plone>=1.0.0a1", False],
    ],
)
@pytest.mark.vcr()
def test_get_package_constraints(
    existing_pins,
    core_package: str,
    core_package_version: str,
    constraint: str,
    is_present: bool,
):
    func = const_utils.get_package_constraints
    result = func(core_package, core_package_version, existing_pins)
    assert (constraint in result) is is_present


def test_get_package_constraints_excludes_existing_pins(monkeypatch):
    """Existing pins (including override-dependencies) must not appear in output."""
    from repoplone.utils.dependencies import pyproject as pyproject_utils

    src = """
[project]
name = "demo"
version = "0.0.0"
dependencies = ["Products.CMFPlone==6.1.0"]

[tool.uv]
override-dependencies = ["urllib3==2.0.0"]
"""
    data = tomlkit.parse(src)
    existing_pins = pyproject_utils.get_all_pinned_dependencies(data)

    monkeypatch.setattr(
        const_utils,
        "pypi_package_versions",
        lambda name: ["6.1.0"],
    )
    monkeypatch.setattr(
        const_utils,
        "get_base_constraints",
        lambda name, version: [
            "Products.CMFPlone==6.1.0",
            "urllib3==1.9.0",
            "requests==2.32.3",
        ],
    )

    result = const_utils.get_package_constraints(
        "Products.CMFPlone", "6.1.0", existing_pins
    )

    # Excluded — present in override-dependencies
    assert "urllib3==1.9.0" not in result
    assert not any(line.startswith("urllib3") for line in result)
    # Kept — the package being upgraded
    assert "Products.CMFPlone==6.1.0" in result
    # Kept — not pinned anywhere locally
    assert "requests==2.32.3" in result


@pytest.mark.parametrize(
    "lines,existing,expected",
    [
        # Sort is by canonical name (case-insensitive, hyphens == underscores == dots)
        (
            ["Zope==5.10", "plone==6.0", "Products.CMFPlone==6.1"],
            [],
            ["plone==6.0", "Products.CMFPlone==6.1", "Zope==5.10"],
        ),
        # Existing value replaces upstream when same package (case-insensitive lookup)
        (
            ["zope==5.10"],
            ["Zope==5.8"],
            ["Zope==5.8"],
        ),
        # Existing extras not in upstream are appended and sorted
        (
            ["plone==6.0"],
            ["zope==5.8", "plone==5.9"],
            ["plone==5.9", "zope==5.8"],
        ),
    ],
)
def test_parse_constraints(lines: list, existing: list, expected: list):
    result = const_utils.parse_constraints(lines, existing)
    assert result == expected


@pytest.mark.parametrize(
    "core_package,raises",
    [
        ["Plone", False],
        ["Products.CMFPlone", False],
        ["kitconcept.core", False],
        ["kitconcept.intranet", False],
        ["kitconcept.site", False],
        ["kitconcept.website", False],
        ["portalbrasil.core", False],
        ["portalbrasil.devsite", False],
        ["portalbrasil.intranet", False],
        ["portalbrasil.legislativo", False],
        ["foo.bar", True],
    ],
)
def test_get_constraint_info(core_package: str, raises: bool):
    func = const_utils.get_constraint_info
    if raises:
        with pytest.raises(AttributeError) as exc:
            func(core_package)
        assert f"{core_package} is not supported at the moment." in str(exc)
    else:
        result = func(core_package)
        assert isinstance(result, dict)
