from pathlib import Path
from repoplone.utils import python_release as pr

import pytest


BASE_FOLDER = (
    "dist/",
    "dist/foo_bar-1.0.0-py3-none-any.whl",
    "dist/foo_bar-1.0.0-py3-none-any.tar.gz",
    "dist/foo_bar-1.0.1-py3-none-any.whl",
    "dist/foo_bar-1.0.1-py3-none-any.tar.gz",
)


@pytest.fixture
def package_factory(test_dir):
    def factory(to_create: tuple[str, ...]) -> list[Path]:
        created: list[Path] = []
        for path in to_create:
            if path.endswith("/"):
                path = path[:-1]
                new_dir = test_dir / path
                new_dir.mkdir(parents=True, exist_ok=True)
                created.append(new_dir)
            else:
                new_file = test_dir / path
                new_file.write_text("")
                created.append(new_file)
        return created

    return factory


@pytest.fixture
def dist_folder_contents(package_factory) -> list[Path]:
    contents = package_factory(BASE_FOLDER)
    return contents


def test__dist_folder_exists(dist_folder_contents):
    folder = pr._dist_folder()
    assert folder is not None
    assert folder in dist_folder_contents


def test__dist_folder_does_not_exists(test_dir):
    folder = pr._dist_folder()
    assert folder is None


@pytest.mark.parametrize(
    "version,total",
    (
        ("", 4),  # All versions
        ("1.0.0", 2),  # 1.0.0 version files
        ("1.0.1", 2),  # 1.0.1 version files
        ("2.0.0", 0),  # 2.0.0 version files
    ),
)
def test_list_release_files(dist_folder_contents, version: str, total: int):
    results = pr.list_release_files(version=version)
    assert len(results) == total


def test_remove_release_files(dist_folder_contents):
    folder = dist_folder_contents[0]
    total_files_before = len(list(folder.glob("*")))
    # Remove files
    pr.remove_release_files()
    total_files_after = len(list(folder.glob("*")))
    assert total_files_before > total_files_after
    assert total_files_after == 0


def test_remove_release_files_with_list(dist_folder_contents):
    folder = dist_folder_contents.pop(0)
    total_files_before = len(list(folder.glob("*")))
    # Remove files
    pr.remove_release_files(files=dist_folder_contents)
    total_files_after = len(list(folder.glob("*")))
    assert total_files_before > total_files_after
    assert total_files_after == 0
