from repoplone.cli import app
from typer.testing import CliRunner

import pytest


runner = CliRunner()

CACHED_OUTPUT = ""


@pytest.fixture
def set_environment_variables(monkeypatch):
    """Remove environment variables that could interfere with the tests."""
    to_remove = ["GITHUB_TOKEN", "UV_PUBLISH_TOKEN", "NPM_TOKEN"]

    def func(env_vars: dict[str, str]):
        for var in to_remove:
            monkeypatch.delenv(var, raising=False)
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

    return func


@pytest.fixture
def complete_release_flow(
    bust_path_cache,
    test_internal_project,
    initialize_repo,
    set_environment_variables,
):
    global CACHED_OUTPUT
    if not CACHED_OUTPUT:
        env_vars = {}
        cli_input = "y\n1\ny\ny\ny\ny\n"
        set_environment_variables(env_vars)
        # Initialize repository
        initialize_repo(test_internal_project)
        result = runner.invoke(app, ["release"], input=cli_input)
        CACHED_OUTPUT = result.output
    return CACHED_OUTPUT


def test_release_help(bust_path_cache, test_public_project):
    result = runner.invoke(app, ["release", "--help"])
    assert result.exit_code == 0
    output = result.stdout
    assert "release [OPTIONS] [DESIRED_VERSION] COMMAND" in output
    assert "Could be the version" in output


@pytest.mark.parametrize(
    "env_vars, expected_strings",
    [
        (
            {},
            [
                "- GITHUB_TOKEN is not present or does not have correct permissions",
                "- You are not authenticated to PyPi using UV",
                "- You are not authenticated to NPM",
            ],
        ),  # No environment variables
        (
            {"GITHUB_TOKEN": "fake_token"},
            [
                "- Could not find a valid origin pointing to a GitHub repository",
                "- You are not authenticated to PyPi using UV",
                "- You are not authenticated to NPM",
            ],
        ),  # Only GITHUB_TOKEN
    ],
)
def test_release_sanity(
    bust_path_cache,
    test_public_project,
    set_environment_variables,
    env_vars: dict[str, str],
    expected_strings: list[str],
):
    set_environment_variables(env_vars)
    result = runner.invoke(app, ["release"])
    assert result.exit_code == 1
    output = result.output
    assert "\nRelease fake-distribution\n" in output
    for expected in expected_strings:
        assert expected in output


@pytest.mark.parametrize(
    "env_vars,cli_input,expected_exit_code,expected_strings",
    [
        (
            {},
            "",
            1,
            [
                "- GITHUB_TOKEN is not present or does not have correct permissions",
                "Do you want to continue the release? [y/n] (y)",
                "Aborted.",
            ],
        ),  # No input
        (
            {},
            "n\n",
            0,
            [
                "- GITHUB_TOKEN is not present or does not have correct permissions",
                "Do you want to continue the release? [y/n] (y)",
                "Exiting now",
            ],
        ),  # explicit no
        (
            {},
            "y\n",
            1,
            [
                "- GITHUB_TOKEN is not present or does not have correct permissions",
                "Do you want to continue the release? [y/n] (y)",
                "01/09 Select the next version",
                "1 - 1.0.0a1 (a)",
            ],
        ),  # explicit yes, no version selected
        (
            {},
            "y\n1\n",
            1,
            [
                "- GITHUB_TOKEN is not present or does not have correct permissions",
                "Do you want to continue the release? [y/n] (y)",
                "01/09 Select the next version",
                "1 - 1.0.0a1 (a)",
                "- Bump version from 1.0.0a0 to 1.0.0a1",
                "Aborted",
            ],
        ),  # explicit yes, select version
        (
            {},
            "y\n1\ny\ny\n",
            1,
            [
                "- GITHUB_TOKEN is not present or does not have correct permissions",
                "Do you want to continue the release? [y/n] (y)",
                "01/09 Select the next version",
                "1 - 1.0.0a1 (a)",
                "03/09 Display Changelog",
                "- Initial implementation @plone",
                "08/09 Create GitHub release",
                "Aborted",
            ],
        ),  # explicit yes, select version, confirm version, confirm changelog
    ],
)
def test_release_confirmation(
    bust_path_cache,
    test_internal_project,
    initialize_repo,
    set_environment_variables,
    env_vars: dict[str, str],
    cli_input: str,
    expected_exit_code: int,
    expected_strings: list[str],
):
    set_environment_variables(env_vars)
    # Initialize repository
    initialize_repo(test_internal_project)
    result = runner.invoke(app, ["release"], input=cli_input)
    assert result.exit_code == expected_exit_code
    output = result.output
    assert "\nRelease fake-project\n" in output
    for expected in expected_strings:
        assert expected in output


@pytest.mark.parametrize(
    "expected_string",
    [
        "- GITHUB_TOKEN is not present or does not have correct permissions",
        "Do you want to continue the release? [y/n] (y)",
        "01/09 Select the next version",
        "1 - 1.0.0a1 (a)",
        "03/09 Display Changelog",
        "- Initial implementation @plone",
        "08/09 Create GitHub release",
    ],
)
def test_complete_release_flow(complete_release_flow, expected_string: str):
    assert expected_string in complete_release_flow
