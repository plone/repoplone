from repoplone import _types as t

import os
import re
import requests


def get_token() -> str | None:
    """Check if this environment has the GITHUB_TOKEN set."""
    return os.getenv("GITHUB_TOKEN")


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
