import pytest


@pytest.fixture
def settings(test_public_project, bust_path_cache):
    from repoplone.settings import get_settings

    return get_settings()


@pytest.fixture
def settings_root_changelog(test_project_root_changelog, bust_path_cache):
    from repoplone.settings import get_settings

    return get_settings()
