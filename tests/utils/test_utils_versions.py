from repoplone.utils import _path
from repoplone.utils import versions

import pytest


@pytest.mark.parametrize(
    "python_version,expected",
    [
        ["1.0.0a0", "1.0.0-alpha.0"],
        ["1.0.0b1", "1.0.0-beta.1"],
        ["1.0.0rc1", "1.0.0-rc.1"],
        ["1.0.0", "1.0.0"],
        ["202503.1", "202503.1.0"],
        ["202512.1", "202512.1.0"],
    ],
)
def test_convert_python_node_version(python_version: str, expected: str):
    func = versions.convert_python_node_version
    result = func(python_version)
    assert result == expected


def test_repository_version(test_public_project, bust_path_cache, settings):
    func = versions.get_repository_version
    result = func(settings)
    assert result == "1.0.0a0"


def test_get_backend_version(test_public_project, bust_path_cache):
    backend_path = _path.get_root_path() / "backend"
    func = versions.get_backend_version
    result = func(backend_path)
    assert result == "1.0.0a0"


def test_get_frontend_version(test_public_project, bust_path_cache):
    package_path = _path.get_root_path() / "frontend" / "packages" / "fake-distribution"
    func = versions.get_frontend_version
    result = func(package_path)
    assert result == "1.0.0-alpha.0"


@pytest.mark.parametrize(
    "version,expected",
    [
        ["1.0.0a1", "1.0.0a1"],
        ["1.0.0b1", "1.0.0b1"],
        ["1.0.0rc1", "1.0.0rc1"],
        ["1.0.0", "1.0.0"],
    ],
)
def test_update_backend_version(
    test_public_project, bust_path_cache, version: str, expected: str
):
    backend_path = _path.get_root_path() / "backend"
    func = versions.update_backend_version
    result = func(backend_path, version)
    assert result == expected


@pytest.mark.parametrize(
    "desired_version,original_version,expected",
    [
        ["a", "1.0.0a0", "1.0.0a1"],
        ["b", "1.0.0a0", "1.0.0b0"],
        ["rc", "1.0.0a0", "1.0.0rc0"],
        ["major", "1.0.0a0", "2.0.0"],
        ["minor", "1.0.0a0", "1.1.0"],
        ["major,a", "1.0.0a0", "2.0.0a0"],
        ["1.0.0a1", "1.0.0a0", "1.0.0a1"],
    ],
)
def test_next_version(desired_version: str, original_version: str, expected: str):
    result = versions.next_version(desired_version, original_version)
    assert result == expected


@pytest.mark.parametrize(
    "desired_version,original_version",
    [
        ["1.0.0a1", "1.0.0a2"],
        ["1.0.0a1", "2.0.0"],
    ],
)
def test_next_version_raise_value_error(desired_version: str, original_version: str):
    with pytest.raises(ValueError) as exc:
        versions.next_version(desired_version, original_version)
    expected = (
        f"Version `{desired_version}` is not higher than "
        f"the original version `{original_version}`"
    )
    assert expected in str(exc)
