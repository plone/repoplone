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
def get_root_path() -> Path:
    return (Path().cwd()).resolve()
