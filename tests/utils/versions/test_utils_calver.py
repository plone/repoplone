from datetime import date
from repoplone.utils.versions import calver

import pytest


TODAY = date.today().strftime("%Y%m%d")


@pytest.mark.parametrize(
    "bump",
    [
        "calver",
    ],
)
def test_bumps(bump: str):
    func = calver.bumps
    result = func()
    assert bump in result


@pytest.mark.parametrize(
    "desired_version,original_version,expected",
    [
        ["calver", f"{TODAY}.1", f"{TODAY}.2"],
        ["calver", "20250605.1", f"{TODAY}.1"],
    ],
)
def test_next_version(desired_version: str, original_version: str, expected: str):
    result = calver.next_version(desired_version, original_version)
    assert result == expected
