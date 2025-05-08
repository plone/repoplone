from pathlib import Path
from repoplone.utils.dependencies import frontend as frontend_utils

import pytest


@pytest.fixture
def frontend_path(test_public_project) -> Path:
    return test_public_project / "frontend"


@pytest.mark.parametrize(
    "package_name,expected",
    [
        ["@plone/volto", "18.14.1"],
        ["@plonegovbr/volto-social-media", "2.0.0-alpha.5"],
    ],
)
def test_package_version(frontend_path, package_name: str, expected: str):
    func = frontend_utils.package_version
    result = func(frontend_path, package_name)
    assert result == expected
