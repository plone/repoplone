from pathlib import Path
from repoplone import _types as t
from repoplone import exceptions
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
        ["kitconcept.site", True],
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


def test_get_constraint_info_warning(monkeypatch, capsys):
    """A package carrying a ``warning`` prints it and is still returned."""
    monkeypatch.setitem(
        const_utils.PACKAGE_CONSTRAINTS,
        "fake.warn",
        {"type": "uv", "url": "http://example.com", "warning": "deprecated, move on"},
    )
    result = const_utils.get_constraint_info("fake.warn")
    assert result["warning"] == "deprecated, move on"
    assert "deprecated, move on" in capsys.readouterr().out


def test__get_uv_constraints_version(monkeypatch):
    """A tagged version keeps the URL and appends the package ``==`` pin."""
    captured = {}

    def fake_remote(url: str):
        captured["url"] = url
        return (["plone.api==1.0"], ["Zope==5.10"])

    monkeypatch.setattr(const_utils, "get_remote_uv_dependencies", fake_remote)
    url = "https://example.com/refs/tags/1.0.0/backend/pyproject.toml"
    result = const_utils._get_uv_constraints(url, "kitconcept.core", "1.0.0")
    assert captured["url"] == url
    assert "kitconcept.core==1.0.0" in result


def test__get_uv_constraints_branch(monkeypatch):
    """A ``@branch`` rewrites the URL to ``/heads/`` and skips the ``==`` pin."""
    captured = {}

    def fake_remote(url: str):
        captured["url"] = url
        return (["plone.api==1.0"], ["Zope==5.10"])

    monkeypatch.setattr(const_utils, "get_remote_uv_dependencies", fake_remote)
    url = "https://example.com/refs/tags/@main/backend/pyproject.toml"
    result = const_utils._get_uv_constraints(url, "kitconcept.core", "@main")
    assert captured["url"] == (
        "https://example.com/refs/heads/main/backend/pyproject.toml"
    )
    assert not any(line.startswith("kitconcept.core==") for line in result)


def test__get_pip_constraints_success(monkeypatch):
    monkeypatch.setattr(
        const_utils,
        "resolve_dependencies",
        lambda *args, **kwargs: ([], ["Zope==5.10", "plone==6.0"]),
    )
    result = const_utils._get_pip_constraints("http://example.com", "Plone", "6.0")
    assert result == ["Zope==5.10", "plone==6.0"]


def test__get_pip_constraints_failure(monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr(const_utils, "resolve_dependencies", boom)
    with pytest.raises(exceptions.RepoPloneExternalException) as exc:
        const_utils._get_pip_constraints("http://example.com", "Plone", "6.0")
    assert "Failed to fetch constraints" in str(exc)


@pytest.mark.parametrize("constraints_type", ["pip", "uv"])
def test_get_base_constraints_dispatch(monkeypatch, constraints_type: str):
    """``get_base_constraints`` dispatches on the configured constraints type."""
    monkeypatch.setitem(
        const_utils.PACKAGE_CONSTRAINTS,
        "fake.pkg",
        {"type": constraints_type, "url": "http://example.com/{version}"},
    )
    monkeypatch.setattr(
        const_utils, "_get_pip_constraints", lambda *args: ["pip-result"]
    )
    monkeypatch.setattr(const_utils, "_get_uv_constraints", lambda *args: ["uv-result"])
    result = const_utils.get_base_constraints("fake.pkg", "1.0")
    assert result == [f"{constraints_type}-result"]


def test_get_base_constraints_invalid_type(monkeypatch):
    monkeypatch.setitem(
        const_utils.PACKAGE_CONSTRAINTS,
        "fake.bad",
        {"type": "conda", "url": "http://example.com/{version}"},
    )
    with pytest.raises(AttributeError) as exc:
        const_utils.get_base_constraints("fake.bad", "1.0")
    assert "invalid constraints type" in str(exc)


def test_parse_constraints_skips_comments_and_blanks():
    """Comment and blank lines are dropped from the parsed constraints."""
    result = const_utils.parse_constraints(["# a comment", "", "   ", "Zope==5.10"], [])
    assert result == ["Zope==5.10"]


def test_get_package_constraints_version_not_available(monkeypatch):
    """An unknown version raises before any constraint is resolved."""
    monkeypatch.setattr(const_utils, "pypi_package_versions", lambda name: ["6.0.0"])
    with pytest.raises(RuntimeError) as exc:
        const_utils.get_package_constraints("Products.CMFPlone", "9.9.9", {})
    assert "9.9.9 not available" in str(exc)


def test_get_package_constraints_skips_blank_and_comment_lines(monkeypatch):
    """Blank and comment lines in the resolved constraints are filtered out."""
    monkeypatch.setattr(const_utils, "pypi_package_versions", lambda name: ["6.1.0"])
    monkeypatch.setattr(
        const_utils,
        "get_base_constraints",
        lambda name, version: [
            "Products.CMFPlone==6.1.0",
            "",
            "# comment",
            "requests==2.0",
        ],
    )
    result = const_utils.get_package_constraints("Products.CMFPlone", "6.1.0", {})
    assert "Products.CMFPlone==6.1.0" in result
    assert "requests==2.0" in result
    assert "" not in result
    assert not any(line.startswith("#") for line in result)


def test_get_package_constraints_branch_skips_pypi_check(monkeypatch):
    """A ``@branch`` install never queries PyPI for available versions."""

    def boom(name):
        raise AssertionError("PyPI should not be queried for a branch install")

    monkeypatch.setattr(const_utils, "pypi_package_versions", boom)
    monkeypatch.setattr(
        const_utils, "get_base_constraints", lambda name, version: ["requests==2.0"]
    )
    result = const_utils.get_package_constraints("kitconcept.core", "@main", {})
    assert result == ["requests==2.0"]
