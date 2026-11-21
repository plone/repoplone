from contextlib import contextmanager
from functools import cache
from pathlib import Path

import os


@contextmanager
def change_cwd(path: Path):
    """Sets the cwd within the context."""
    origin = Path().cwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(origin)


@cache
def get_cwd_path() -> Path:
    return (Path().cwd()).resolve()


def frontend_root(root_path: Path, package_path: Path) -> Path:
    """Return the workspace root of a frontend package.

    This is the directory holding ``mrs.developer.json``, ``distribution.json``
    and the frontend-wide ``CHANGELOG.md`` -- one level above ``packages/`` in
    the usual ``frontend/packages/<name>`` layout.

    Deriving it by walking two levels up only works for that layout. A package
    declared directly under the repository root, such as ``path = "frontend"``,
    would walk out of the repository entirely, so the conventional
    ``<root>/frontend`` is used whenever walking up leaves the repository.

    :param root_path: Repository root.
    :param package_path: Absolute path of the frontend package.
    :returns: The frontend workspace root.
    """
    candidate = package_path.parent.parent
    if candidate == root_path or not candidate.is_relative_to(root_path):
        return root_path / "frontend"
    return candidate
