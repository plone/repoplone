from pathlib import Path
from repoplone.utils.dependencies import frontend as frontend_utils

import pytest


@pytest.fixture
def frontend_path(test_frontend_base_package) -> Path:
    return test_frontend_base_package / "frontend"


@pytest.fixture
def mrs_developer_data(frontend_path: Path) -> dict:
    func = frontend_utils._load_mrs_developer
    data = func(frontend_path)
    return data


@pytest.mark.parametrize(
    "package_name,expected",
    [
        ["@plone/volto", "18.14.1"],
        [
            "@kitconcept/core",
            "2.0.0-alpha.2",
        ],  # Information comes from mrs.developer.json and is transformed from 2.0.0a2
    ],
)
def test_package_version(frontend_path, package_name: str, expected: str):
    func = frontend_utils.package_version
    result = func(frontend_path, package_name)
    assert result == expected


@pytest.mark.parametrize(
    "package_name",
    [
        "@plone/volto",
        "@kitconcept/core",
    ],
)
def test__get_entry_mrs_developer(mrs_developer_data, package_name: str):
    func = frontend_utils._get_entry_mrs_developer
    result = func(mrs_developer_data, package_name)
    assert isinstance(result, dict)


@pytest.mark.parametrize(
    "package_name,transform,expected",
    [
        ["@plone/volto", False, "18.14.1"],
        ["@plone/volto", True, "18.14.1"],
        [
            "@kitconcept/core",
            True,
            "2.0.0-alpha.2",
        ],
        [
            "@kitconcept/core",
            False,
            "2.0.0a2",
        ],
    ],
)
def test__parse_version_from_mrs_developer(
    mrs_developer_data, package_name: str, transform: bool, expected: str
):
    func = frontend_utils._parse_version_from_mrs_developer
    checkout_entry = frontend_utils._get_entry_mrs_developer(
        mrs_developer_data, package_name
    )
    result = func(checkout_entry, transform=transform)
    assert result == expected
