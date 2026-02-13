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


@pytest.mark.parametrize(
    "path,expected",
    [
        ["pyproject/distribution.toml", True],
        ["pyproject/package.toml", False],
        ["pyproject/project.toml", True],
    ],
)
def test_pyproject_uv_managed(get_resource_file, path: str, expected: str):
    func = pyproject_utils.managed_by_uv
    pyproject_path = get_resource_file(path)
    result = func(pyproject_path)
    assert result == expected


@pytest.mark.parametrize(
    "version,expected",
    [
        ["3.7", False],
        ["3.8", False],
        ["3.9", False],
        ["3.10", False],
        ["3.11", True],
        ["3.12", True],
        ["3.13", True],
    ],
)
def test_python_versions(pyproject_toml, version: str, expected: bool):
    func = pyproject_utils.python_versions
    result = func(pyproject_toml)
    assert (version in result) is expected


@pytest.mark.parametrize(
    "version,expected",
    [
        ["6.0", False],
        ["6.1", True],
        ["6.2", False],
    ],
)
def test_plone_versions(pyproject_toml, version: str, expected: bool):
    func = pyproject_utils.plone_versions
    result = func(pyproject_toml)
    assert (version in result) is expected


@pytest.mark.parametrize(
    "python_versions,plone_versions",
    [
        (["3.11", "3.12", "3.13", "3.14"], ["6.0", "6.1", "6.2"]),
        (["3.10", "3.11", "3.12"], ["6.0"]),
    ],
)
def test__update_classifiers(
    pyproject_toml, python_versions: list[str], plone_versions: list[str]
):
    func = pyproject_utils._update_classifiers
    # Update classifiers in place
    func(pyproject_toml, python_versions, plone_versions)
    # Check if classifiers were updated
    python_versions_in_file = pyproject_utils.python_versions(pyproject_toml)
    assert set(python_versions_in_file) == set(python_versions)
    plone_versions_in_file = pyproject_utils.plone_versions(pyproject_toml)
    assert set(plone_versions_in_file) == set(plone_versions)
