from repoplone.utils import _github as ghutils

import pytest


@pytest.mark.parametrize(
    "remote_origin,expected",
    [
        ["git@github.com:owner/repo.git", "owner/repo"],
        ["https://github.com/owner/repo.git", "owner/repo"],
        ["https://github.com/owner/repo", "owner/repo"],
    ],
)
def test__get_owner_repo(remote_origin: str, expected: str):
    func = ghutils._get_owner_repo
    result = func(remote_origin)
    assert result == expected


@pytest.mark.parametrize(
    "remote_origin,expected",
    [
        [
            "git@github.com:owner/repo.git",
            "https://github.com/owner/repo/issues",
        ],
        [
            "https://github.com/owner/repo.git",
            "https://github.com/owner/repo/issues",
        ],
        [
            "https://github.com/owner/repo",
            "https://github.com/owner/repo/issues",
        ],
        ["https://gitlab.com/owner/repo.git", ""],
        ["git@gitlab.com:owner/repo.git", ""],
        ["", ""],
    ],
)
def test_derive_issues_url(remote_origin: str, expected: str):
    assert ghutils.derive_issues_url(remote_origin) == expected
