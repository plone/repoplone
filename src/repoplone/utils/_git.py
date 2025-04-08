from git import InvalidGitRepositoryError
from git import Remote
from git import Repo
from git import Tag
from pathlib import Path
from repoplone import logger


def _initialize_repo_for_project(path: Path) -> Repo:
    """Return the repository for a project."""
    repo = Repo.init(path)
    return repo


def repo_for_project(path: Path) -> Repo:
    """Return the repository for a project."""
    repo = Repo(path)
    return repo


def _get_remote(repo: Repo) -> Remote | None:
    try:
        origin = repo.remote("origin")
    except ValueError:
        logger.info("No origin for this repo")
        origin = None
    return origin


def remote_origin(path: Path) -> str:
    """Return the url for the remote origin."""
    try:
        repo = repo_for_project(path)
        origin = _get_remote(repo)
    except InvalidGitRepositoryError:
        origin = None
    return origin.url if origin else ""


def push_changes(repo: Repo, ref: Tag | None = None):
    if not (origin := _get_remote(repo)):
        return
    if ref:
        origin.push(ref)
    else:
        origin.push()


def commit_pending_changes(repo: Repo, message: str):
    git_cmd = repo.git
    git_cmd.commit("-am", message)


def repo_has_version(repo: Repo, version: str) -> bool:
    # Fetch existing tags
    origin = repo.remote("origin")
    if origin:
        origin.fetch()
    # List tags
    tags: list[Tag] = repo.tags
    names = [tag.name for tag in tags]
    return bool(version in names)


def create_version_tag(repo: Repo, version: str, message: str) -> Tag:
    # Create tag
    tag = repo.create_tag(version, message=message)
    # Push tag
    push_changes(repo, tag)
    return tag


def finish_release(repo: Repo, version: str) -> Tag:
    message = f"Release {version}"
    commit_pending_changes(repo, message)
    tag = create_version_tag(repo, version, message)
    push_changes(repo)
    return tag
