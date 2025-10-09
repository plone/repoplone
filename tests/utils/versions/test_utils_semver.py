from repoplone.utils.versions import semver

import pytest


@pytest.mark.parametrize(
    "bump",
    [
        "release",
        "major",
        "minor",
        "micro",
        "patch",
        "fix",
        "a",
        "b",
        "rc",
        "post",
        "dev",
    ],
)
def test_bumps(bump: str):
    func = semver.bumps
    result = func()
    assert bump in result


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
    result = semver.next_version(desired_version, original_version)
    assert result == expected


@pytest.mark.parametrize(
    "major, minor, patch, pre, build, expected",
    [
        [1, 0, 0, None, None, "1.0.0"],
        [1, 0, 0, "alpha.1", None, "1.0.0-alpha.1"],
        [1, 0, 0, "alpha.2", None, "1.0.0-alpha.2"],
        [1, 0, 0, "alpha.2", 3, "1.0.0-alpha.2+3"],
    ],
)
def test_version_from_parts(
    major: int,
    minor: int,
    patch: int,
    pre: str | None,
    build: int | None,
    expected: str,
):
    result = semver.version_from_parts(major, minor, patch, pre, build)
    assert result == expected
