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


@pytest.fixture
def pyproject_overrides(get_resource_file) -> tomlkit.TOMLDocument:
    pyproject_path = get_resource_file("pyproject/overrides.toml")
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


def test__process_requirements_tool_uv_override_dependencies(pyproject_overrides):
    result = pyproject_utils._process_requirements(
        pyproject_overrides, "tool.uv.override-dependencies"
    )
    assert len(result) == 2
    assert {req.name for req in result} == {"urllib3", "pytest-plone"}


def test__process_requirements_missing_path_returns_empty():
    data = tomlkit.parse('[project]\nname = "demo"\n')
    result = pyproject_utils._process_requirements(
        data, "tool.uv.override-dependencies"
    )
    assert result == []


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


def test_get_all_pinned_dependencies_includes_override_dependencies(
    pyproject_overrides,
):
    result = pyproject_utils.get_all_pinned_dependencies(pyproject_overrides)
    assert "urllib3" in result
    assert str(result["urllib3"].specifier) == "==2.0.0"
    assert "pytest-plone" in result
    assert str(result["pytest-plone"].specifier) == "==1.0.0"


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
        (["3.10", "3.11", "3.11", "3.12"], ["6.0", "6.0"]),
    ],
)
def test__update_classifiers(
    pyproject_toml, python_versions: list[str], plone_versions: list[str]
):
    """Test that classifiers are updated correctly in the pyproject.toml.

    We should never have duplicate classifiers, even if the input contain duplicates.
    """
    func = pyproject_utils._update_classifiers
    # Update classifiers in place
    func(pyproject_toml, python_versions, plone_versions)
    # Updating a second time should not duplicate classifiers
    func(pyproject_toml, python_versions, plone_versions)
    # Check if classifiers were updated
    python_versions_in_file = pyproject_utils.python_versions(pyproject_toml)
    assert set(python_versions_in_file) == set(python_versions)
    plone_versions_in_file = pyproject_utils.plone_versions(pyproject_toml)
    assert set(plone_versions_in_file) == set(plone_versions)
    assert len(python_versions_in_file) == len(set(python_versions))
    assert len(plone_versions_in_file) == len(set(plone_versions))


@pytest.mark.parametrize(
    "python_versions,plone_versions",
    [
        (["3.11", "3.12", "3.13", "3.14"], ["6.0", "6.1", "6.2"]),
        (["3.10", "3.11", "3.12"], ["6.0"]),
        (["3.10", "3.11", "3.11", "3.12"], ["6.0", "6.0"]),
    ],
)
def test__update_classifiers_cleanup_license(
    pyproject_toml, python_versions: list[str], plone_versions: list[str]
):
    """Test that classifiers remove duplication of license information."""
    func = pyproject_utils._update_classifiers
    # Check current
    assert pyproject_utils.license_from_classifier(pyproject_toml) != []
    assert pyproject_utils.license_from_project(pyproject_toml) != ""
    # Update classifiers in place
    func(pyproject_toml, python_versions, plone_versions)
    # Check after
    assert pyproject_utils.license_from_classifier(pyproject_toml) == []
    assert pyproject_utils.license_from_project(pyproject_toml) != ""


def test__get_table_invalid_raises():
    """A key pointing at a scalar (not a table) raises ``ValueError``."""
    data = tomlkit.parse('project = "scalar"')
    with pytest.raises(ValueError, match="Invalid data"):
        pyproject_utils._get_table(data, "project")


def test__process_requirements_handles_navigation_error():
    """A navigation error while walking the dotted key yields an empty list."""

    class Boom(dict):
        def get(self, *args, **kwargs):
            raise ValueError("boom")

    result = pyproject_utils._process_requirements(Boom(), "project.dependencies")
    assert result == []


def test__get_uv_table_missing_returns_empty():
    data = tomlkit.parse('[project]\nname = "demo"\n')
    result = pyproject_utils._get_uv_table(data)
    assert not result


def test__get_uv_sources_table_existing():
    data = tomlkit.parse('[tool.uv.sources]\nfoo = { git = "http://x" }\n')
    result = pyproject_utils._get_uv_sources_table(data)
    assert "foo" in result


def test__get_uv_sources_table_missing():
    data = tomlkit.parse('[project]\nname = "demo"\n')
    result = pyproject_utils._get_uv_sources_table(data)
    assert not result


def test__ensure_uv_table_creates_when_missing():
    data = tomlkit.parse('[project]\nname = "demo"\n')
    table = pyproject_utils._ensure_uv_table(data)
    table["foo"] = "bar"
    # The created table is attached to the document.
    assert data["tool"]["uv"]["foo"] == "bar"


def test__ensure_uv_table_returns_existing():
    data = tomlkit.parse("[tool.uv]\nmanaged = false\n")
    table = pyproject_utils._ensure_uv_table(data)
    assert table.get("managed") is False


def test_get_remote_uv_dependencies_mocked(monkeypatch):
    """Pinned dependencies and constraints are read from a remote pyproject."""
    src = """
[project]
name = "demo"
dependencies = ["plone.api==1.0", "requests"]

[tool.uv]
constraint-dependencies = ["Zope==5.10"]
"""

    class Resp:
        content = src.encode("utf-8")

    monkeypatch.setattr(pyproject_utils, "get_remote_data", lambda url: Resp())
    deps, constraints = pyproject_utils.get_remote_uv_dependencies("http://example.com")
    # Only pinned dependencies are returned.
    assert deps == ["plone.api==1.0"]
    assert constraints == ["Zope==5.10"]


def test_current_base_package_missing(pyproject_path):
    result = pyproject_utils.current_base_package(pyproject_path, "does.not.exist")
    assert result is None


def test__uv_add_source_package_with_repository():
    data = tomlkit.parse('[project]\nname = "demo"\n')
    pyproject_utils._uv_add_source_package(data, "kitconcept.core", "@main")
    source = data["tool"]["uv"]["sources"]["kitconcept.core"]
    assert source["git"] == "https://github.com/kitconcept/kitconcept-core"
    assert source["branch"] == "main"
    assert source["subdirectory"] == "backend"


def test__uv_add_source_package_without_subdirectory(monkeypatch):
    from repoplone.utils.dependencies import constraints as const_utils

    monkeypatch.setitem(
        const_utils.PACKAGE_CONSTRAINTS,
        "fake.repo",
        {
            "type": "uv",
            "url": "http://example.com",
            "repository": {"url": "https://github.com/x/y"},
        },
    )
    data = tomlkit.parse('[project]\nname = "demo"\n')
    pyproject_utils._uv_add_source_package(data, "fake.repo", "@dev")
    source = data["tool"]["uv"]["sources"]["fake.repo"]
    assert source["git"] == "https://github.com/x/y"
    assert source["branch"] == "dev"
    assert "subdirectory" not in source


def test__uv_add_source_package_without_repository():
    """A package with no repository info cannot be installed from a branch."""
    data = tomlkit.parse('[project]\nname = "demo"\n')
    with pytest.raises(RuntimeError, match="repository information"):
        pyproject_utils._uv_add_source_package(data, "Products.CMFPlone", "@main")


def test__uv_remove_source_package():
    data = tomlkit.parse('[tool.uv.sources]\nfoo = { git = "http://x" }\n')
    pyproject_utils._uv_remove_source_package(data, "foo")
    assert "foo" not in data["tool"]["uv"]["sources"]
    # Removing a missing package is a no-op.
    pyproject_utils._uv_remove_source_package(data, "missing")


def test__update_dependency_version(pyproject_toml):
    """A regular version pins the package with ``==`` and removes any source."""
    pyproject_utils._update_dependency(pyproject_toml, "Products.CMFPlone", "6.1.1")
    deps = pyproject_utils._get_project_dependencies(pyproject_toml)
    assert str(deps["Products.CMFPlone"].specifier) == "==6.1.1"


def test__update_dependency_branch():
    """A ``@branch`` drops the pin and wires a Git source, keeping other deps."""
    data = tomlkit.parse(
        '[project]\nname = "demo"\n'
        'dependencies = ["kitconcept.core==1.0.0", "plone.api"]\n'
    )
    pyproject_utils._update_dependency(data, "kitconcept.core", "@main")
    deps = pyproject_utils._get_project_dependencies(data)
    assert str(deps["kitconcept.core"].specifier) == ""
    assert "kitconcept.core" in data["tool"]["uv"]["sources"]
    # Unrelated dependencies are preserved untouched.
    assert "plone.api" in deps


def test__update_constraints_creates_table():
    data = tomlkit.parse('[project]\nname = "demo"\n')
    pyproject_utils._update_constraints(data, ["Zope==5.10", "plone==6.0"])
    constraints = list(data["tool"]["uv"]["constraint-dependencies"])
    assert "Zope==5.10" in constraints
    assert "plone==6.0" in constraints


def test__handle_license_classifier_no_license():
    """Without a project license, the license classifiers are left untouched."""
    data = tomlkit.parse('[project]\nname = "demo"\nclassifiers = ["License :: OSI"]\n')
    project = pyproject_utils._get_project_table(data)
    classifiers = {"License :: OSI"}
    pyproject_utils._handle_license_classifier(project, classifiers)
    assert classifiers == {"License :: OSI"}


def test__parse_pyproject():
    result = pyproject_utils._parse_pyproject('[project]\nname = "demo"\n')
    assert result["project"]["name"] == "demo"


def test_parse_pyproject(pyproject_path):
    result = pyproject_utils.parse_pyproject(pyproject_path)
    assert "project" in result


def test_update_pyproject(pyproject_path):
    pyproject_utils.update_pyproject(
        pyproject_path,
        "Products.CMFPlone",
        "6.1.1",
        ["Zope==5.10"],
        python_versions=["3.12", "3.13"],
        plone_versions=["6.1"],
    )
    data = pyproject_utils.parse_pyproject(pyproject_path)
    deps = pyproject_utils._get_project_dependencies(data)
    assert str(deps["Products.CMFPlone"].specifier) == "==6.1.1"
    constraints = list(data["tool"]["uv"]["constraint-dependencies"])
    assert "Zope==5.10" in constraints
    assert "3.13" in pyproject_utils.python_versions(data)


def test_update_pyproject_without_versions(pyproject_path):
    """Classifiers are left untouched when versions are not provided."""
    before = pyproject_utils.python_versions(
        pyproject_utils.parse_pyproject(pyproject_path)
    )
    pyproject_utils.update_pyproject(
        pyproject_path, "Products.CMFPlone", "6.1.1", ["Zope==5.10"]
    )
    data = pyproject_utils.parse_pyproject(pyproject_path)
    constraints = list(data["tool"]["uv"]["constraint-dependencies"])
    assert "Zope==5.10" in constraints
    assert pyproject_utils.python_versions(data) == before
