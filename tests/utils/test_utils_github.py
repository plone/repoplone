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
