from repoplone import _types as t
from repoplone.utils import display as dutils

import os
import re
import requests
import shutil
import subprocess
import sys


# Cache of the token obtained from the gh CLI (and whether the user was asked).
_gh_cli_token_cache: dict = {"asked": False, "token": None}


def _reset_gh_cli_token_cache() -> None:
    """Reset the cached gh CLI token, mostly useful for tests."""
    _gh_cli_token_cache["asked"] = False
    _gh_cli_token_cache["token"] = None


def _token_from_gh_cli() -> str | None:
    """Return a GitHub token from an authenticated ``gh`` CLI session.

    The user is asked, once per session, if repoplone may reuse the token from
    the GitHub CLI. Returns ``None`` if the CLI is missing, there is no
    authenticated session, the user declines, or the run is not interactive
    (we do not want to prompt, or silently reuse credentials, in scripts).
    """
    if _gh_cli_token_cache["asked"]:
        return _gh_cli_token_cache["token"]
    _gh_cli_token_cache["asked"] = True
    if not sys.stdin.isatty():
        return None
    gh_path = shutil.which("gh")
    if not gh_path:
        return None
    try:
        process = subprocess.run(  # noQA: S603
            [gh_path, "auth", "token"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    token = process.stdout.strip()
    if process.returncode != 0 or not token:
        return None
    question = (
        "[bold yellow]GITHUB_TOKEN is not set.[/bold yellow] Use the token from "
        "your authenticated `gh` CLI session instead?"
    )
    if not dutils.confirm(question):
        dutils.indented_print("- Not using the `gh` CLI token")
        return None
    _gh_cli_token_cache["token"] = token
    dutils.indented_print("- Using the token from the `gh` CLI session")
    return token


def get_token() -> str | None:
    """Return the GitHub token, either from GITHUB_TOKEN or the ``gh`` CLI."""
    return os.getenv("GITHUB_TOKEN") or _token_from_gh_cli()


def gh_session() -> requests.Session | None:
    """Return a Session with correct headers for a GitHub REST API call."""
    session = None
    if token := get_token():
        session = requests.Session()
        session.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }
    return session


def _get_owner_repo(remote_origin: str) -> str:
    """Return OWNER/REPO from a remote_origin."""
    pattern = r"^(git@|https:\/\/)github\.com(:|\/)(?P<owner>[^\/]*)\/(?P<repo>.+)$"
    match = re.match(pattern, remote_origin)
    if not match:
        raise ValueError(f"Not a valid GitHub repository {remote_origin}")
    groups = match.groupdict()
    owner = groups["owner"]
    repo = groups["repo"]
    if repo.endswith(".git"):
        repo = repo[:-4]
    return f"{owner}/{repo}"


def derive_issues_url(remote_origin: str) -> str:
    """Return the GitHub issues URL for ``remote_origin``, or an empty string.

    :param remote_origin: Git remote URL (HTTPS or SSH).
    :returns: ``https://github.com/<owner>/<repo>/issues`` when ``remote_origin``
        points at GitHub, otherwise an empty string.
    """
    try:
        owner_repo = _get_owner_repo(remote_origin)
    except ValueError:
        return ""
    return f"https://github.com/{owner_repo}/issues"


def check_token(settings: t.RepositorySettings) -> bool:
    """Check if this environment has the GITHUB_TOKEN set."""
    token = get_token()
    status = False
    if token and (session := gh_session()):
        remote_path = _get_owner_repo(settings.remote_origin)
        response = session.get(f"https://api.github.com/repos/{remote_path}/releases")
        status = response.status_code == 200
    return status


def create_release(
    settings: t.RepositorySettings,
    original_version: str,
    next_version: str,
) -> str:
    if not check_token(settings):
        return (
            f"Release {next_version} not created because GITHUB_TOKEN"
            "is not present or does not have correct permissions"
        )
    changelog = settings._tmp_changelog
    remote_path = _get_owner_repo(settings.remote_origin)
    if session := gh_session():
        payload = {
            "tag_name": next_version,
            "target_commitish": "main",
            "name": next_version,
            "body": changelog,
            "draft": False,
            "prerelease": False,
            "generate_release_notes": False,
        }
        response = session.post(
            f"https://api.github.com/repos/{remote_path}/releases", json=payload
        )
        if response.status_code == 201:
            data = response.json()
            url = data.get("html_url")
            msg = f"Release {next_version} created at {url}"
        else:
            data = response.json()
            msg = (
                f"Release {next_version} failed to be created "
                f"({response.status_code} {data['message']})"
            )
    else:
        msg = f"Release {next_version} failed to be created."
    # Remove tmp changelog
    settings._tmp_changelog = ""
    return msg
