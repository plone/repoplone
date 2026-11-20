from repoplone.utils import _github as ghutils

import subprocess
import sys

import pytest


@pytest.fixture(autouse=True)
def reset_gh_cli_token_cache():
    ghutils._reset_gh_cli_token_cache()
    yield
    ghutils._reset_gh_cli_token_cache()


def _fake_run_factory(returncode: int, stdout: str = "", stderr: str = ""):
    def fake_run(command, *args, **kwargs):
        return subprocess.CompletedProcess(command, returncode, stdout, stderr)

    return fake_run


@pytest.mark.parametrize(
    "env_token, which_result, returncode, stdout, confirmed, expected",
    [
        # GITHUB_TOKEN wins, even with an authenticated gh CLI session
        ["env_token", "gh", 0, "gh_token", True, "env_token"],
        # gh CLI fallback, when the user confirms
        [None, "gh", 0, "gh_token", True, "gh_token"],
        # ...and the user declines
        [None, "gh", 0, "gh_token", False, None],
        # gh is not installed
        [None, None, 0, "gh_token", True, None],
        # gh is installed but not authenticated
        [None, "gh", 1, "", True, None],
        # gh is authenticated but returns no token
        [None, "gh", 0, "", True, None],
    ],
)
def test_get_token_from_gh_cli(
    monkeypatch,
    env_token: str | None,
    which_result: str | None,
    returncode: int,
    stdout: str,
    confirmed: bool,
    expected: str | None,
):
    if env_token:
        monkeypatch.setenv("GITHUB_TOKEN", env_token)
    else:
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    # Pretend we are in an interactive terminal
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(ghutils.shutil, "which", lambda name: which_result)
    monkeypatch.setattr(
        ghutils.subprocess, "run", _fake_run_factory(returncode, stdout)
    )
    monkeypatch.setattr(ghutils.dutils, "confirm", lambda *args, **kwargs: confirmed)
    assert ghutils.get_token() == expected


def test_get_token_gh_cli_prompt_happens_once(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(ghutils.shutil, "which", lambda name: "gh")
    monkeypatch.setattr(ghutils.subprocess, "run", _fake_run_factory(0, "gh_token"))
    asked = []

    def fake_confirm(*args, **kwargs):
        asked.append(True)
        return True

    monkeypatch.setattr(ghutils.dutils, "confirm", fake_confirm)
    assert ghutils.get_token() == "gh_token"
    assert ghutils.get_token() == "gh_token"
    assert len(asked) == 1


def test_get_token_gh_cli_skipped_when_not_interactive(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(ghutils.shutil, "which", lambda name: "gh")
    monkeypatch.setattr(ghutils.subprocess, "run", _fake_run_factory(0, "gh_token"))

    def fail_confirm(*args, **kwargs):
        raise AssertionError("should not prompt when not interactive")

    monkeypatch.setattr(ghutils.dutils, "confirm", fail_confirm)
    assert ghutils.get_token() is None


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
