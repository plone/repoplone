from pathlib import Path

import pytest
import shutil
import tomlkit


RESOURCES = Path(__file__).parent / "_resources"


@pytest.fixture(scope="session")
def test_resources_dir() -> Path:
    return RESOURCES


@pytest.fixture
def test_dir(monkeypatch, tmp_path) -> Path:
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def get_resource_file():
    def func(name: str) -> Path:
        return RESOURCES / name

    return func


@pytest.fixture
def repository_toml_factory(test_dir, get_resource_file):
    def func(filename: str) -> Path:
        src = get_resource_file(filename).read_text()
        dst = test_dir / "repository.toml"
        dst.write_text(src)
        return test_dir

    return func


@pytest.fixture
def toml_parse():
    def func(path: Path) -> dict:
        return tomlkit.parse(path.read_text())

    return func


@pytest.fixture
def update_pyproject():
    from repoplone.utils.dependencies import update_pyproject

    def func(path: Path, package: str, version: str, constraints: list[str]) -> dict:
        update_pyproject(path, package, version, constraints)

    return func


@pytest.fixture
def test_public_project(monkeypatch, tmp_path) -> Path:
    src = RESOURCES / "fake_distribution"
    dst = tmp_path / "fake_distribution"
    shutil.copytree(src, dst)
    monkeypatch.chdir(dst)
    return dst


@pytest.fixture
def test_internal_project(monkeypatch, tmp_path) -> Path:
    src = RESOURCES / "fake-project"
    dst = tmp_path / "fake-project"
    shutil.copytree(src, dst)
    monkeypatch.chdir(dst)
    return dst


@pytest.fixture
def test_internal_project_from_distribution(monkeypatch, tmp_path) -> Path:
    src = RESOURCES / "fake-project-from-distribution"
    dst = tmp_path / "fake-project-from-distribution"
    shutil.copytree(src, dst)
    monkeypatch.chdir(dst)
    return dst


@pytest.fixture
def test_project_root_changelog(monkeypatch, tmp_path) -> Path:
    src = RESOURCES / "fake-project-root-changelog"
    dst = tmp_path / "fake-project-root-changelog"
    shutil.copytree(src, dst)
    monkeypatch.chdir(dst)
    return dst


@pytest.fixture
def bust_path_cache():
    from repoplone.utils import _path

    for name in ("get_cwd_path",):
        func = getattr(_path, name)
        func.cache_clear()


@pytest.fixture
def bust_package_versions_cache():
    from repoplone.utils.dependencies import versions

    for name in ("package_versions",):
        func = getattr(versions, name)
        func.cache_clear()


@pytest.fixture(scope="session")
def vcr_config():
    return {
        "filter_headers": ["authorization"],
        "ignore_localhost": True,
        "record_mode": "once",
    }


@pytest.fixture(scope="session")
def vcr_cassette_dir(request):
    return str(RESOURCES / "vcr")


@pytest.fixture
def settings(test_public_project):
    from repoplone import settings

    return settings.get_settings()


@pytest.fixture
def initialize_repo():
    from git import Repo
    from repoplone.utils import _git

    def func(path: Path) -> Repo:
        repo = _git._initialize_repo_for_project(path)
        # Initial commit
        git_cmd = repo.git
        git_cmd.config("--local", "user.email", "'foo@example.com'")
        git_cmd.config("--local", "user.name", "'John Doe'")
        git_cmd.add(".")
        git_cmd.commit("-m", "Initial commit")
        # Add a tag
        _git.create_version_tag(repo, "1.0.0a0", "Release 1.0.0a0")
        return repo

    return func


@pytest.fixture
def requests_timeout(monkeypatch):
    import requests

    def mock_get(*args, **kwargs):
        raise requests.ConnectTimeout("Connection timed out")

    monkeypatch.setattr(requests, "get", mock_get)
