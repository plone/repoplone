from packaging.requirements import Requirement
from pathlib import Path
from repoplone.utils.dependencies import pyproject as pyproject_utils

import pytest
import tomlkit


@pytest.fixture
def pyproject_path(test_public_project) -> Path:
    return test_public_project / "backend" / "pyproject.toml"


@pytest.fixture
def pyproject_toml(pyproject_path) -> tomlkit.TOMLDocument:
    return tomlkit.parse(pyproject_path.read_text())


@pytest.mark.parametrize(
    "key,total_items",
    [
        ["project.dependencies", 4],
        ["project.optional-dependencies", 5],
        ["dependency-groups", 5],
    ],
)
def test__process_requirements(pyproject_toml, key: str, total_items: int):
    func = pyproject_utils._process_requirements
    result = func(pyproject_toml, key)
    assert isinstance(result, list)
    assert len(result) == total_items
    if total_items:
        assert {isinstance(item, Requirement) for item in result} == {True}


@pytest.mark.parametrize(
    "package,expected",
    [
        ["Products.CMFPlone", "==6.1.0"],
        ["pytest-plone", ">=1.0.0a1"],
    ],
)
def test_get_all_pinned_dependencies(pyproject_toml, package: str, expected: str):
    func = pyproject_utils.get_all_pinned_dependencies
    result = func(pyproject_toml)
    assert package in result
    assert result[package].specifier == expected


@pytest.mark.parametrize(
    "name,specifier,extras",
    [
        ["Products.CMFPlone", "==6.1.0", set()],
        ["plone.api", "", set()],
        ["plone.volto", "", set()],
        ["plone.restapi", "", set()],
    ],
)
def test__get_project_dependencies(
    pyproject_toml, name: str, specifier: str, extras: set
):
    func = pyproject_utils._get_project_dependencies
    result = func(pyproject_toml)
    package = result.get(name)
    assert isinstance(package, Requirement)
    assert package.specifier == specifier
    assert package.extras == extras


@pytest.mark.parametrize(
    "package_name,expected",
    [
        ["Products.CMFPlone", "6.1.0"],
    ],
)
def test_current_base_package(pyproject_path, package_name: str, expected: str):
    func = pyproject_utils.current_base_package
    result = func(pyproject_path, package_name)
    assert result == expected


GH_KC = "https://raw.githubusercontent.com/kitconcept"
GH_PB = "https://raw.githubusercontent.com/portal-br"


@pytest.mark.parametrize(
    "url",
    [
        f"{GH_KC}/kitconcept.intranet/refs/tags/1.0.0a17/backend/pyproject.toml",
        f"{GH_PB}/legislativo/refs/heads/main/backend/pyproject.toml",
    ],
)
@pytest.mark.vcr()
def test_get_remote_uv_dependencies(url: str):
    func = pyproject_utils.get_remote_uv_dependencies
    result = func(url)
    assert isinstance(result, tuple)
    deps = result[0]
    assert isinstance(deps, list)
    assert isinstance(deps[0], str)
    constraints = result[1]
    assert isinstance(constraints, list)
    assert isinstance(constraints[0], str)
