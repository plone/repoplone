from repoplone.cli import app
from typer.testing import CliRunner

import pytest


runner = CliRunner()

CACHED_OUTPUT = ""


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
        cli_input = "y\ny\n1\ny\ny\ny\n"
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
            "y\ny\n",
            1,
            [
                "- GITHUB_TOKEN is not present or does not have correct permissions",
                "Do you want to continue the release? [y/n] (y)",
                "01/08 Display Changelog",
                "   Continue? [y/n] (y)",
            ],
        ),  # explicit yes, confirm changelog
        (
            {},
            "y\ny\n",
            1,
            [
                "- GITHUB_TOKEN is not present or does not have correct permissions",
                "Do you want to continue the release? [y/n] (y)",
                "01/08 Display Changelog",
                "02/08 Next version",
                "1 - 1.0.0a1 (a)",
                "Aborted.",
            ],
        ),  # explicit yes, no version selected
        (
            {},
            "y\ny\n1\n",
            1,
            [
                "- GITHUB_TOKEN is not present or does not have correct permissions",
                "Do you want to continue the release? [y/n] (y)",
                "01/08 Display Changelog",
                "02/08 Next version",
                "   Select the next version",
                "1 - 1.0.0a1 (a)",
                "- Skipping GitHub release creation",
                "- Completed the release of version 1.0.0a1 from version 1.0.0a0",
                "Continue? [y/n] (y):",
                "Aborted.",
            ],
        ),  # explicit yes, select version, no confirmation for goodbye
        (
            {},
            "y\ny\n1\ny\n",
            0,
            [
                "- GITHUB_TOKEN is not present or does not have correct permissions",
                "Do you want to continue the release? [y/n] (y)",
                "01/08 Display Changelog",
                "02/08 Next version",
                "   Select the next version",
                "1 - 1.0.0a1 (a)",
                "- Skipping GitHub release creation",
                "- Completed the release of version 1.0.0a1 from version 1.0.0a0",
            ],
        ),  # explicit yes, select version, confirm and goodbye
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
        "01/08 Display Changelog",
        "- Initial implementation @plone",
        "02/08 Next version",
        "1 - 1.0.0a1 (a)",
        "07/08 Create GitHub release",
    ],
)
def test_complete_release_flow(complete_release_flow, expected_string: str):
    assert expected_string in complete_release_flow
