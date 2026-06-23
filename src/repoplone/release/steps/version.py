from repoplone.release import _types as t
from repoplone.utils import display as dutils
from repoplone.utils import release as utils
from repoplone.utils import versions as vutils
from typing import Any


def _get_next_version(
    settings: t.RepositorySettings, original_version: str, desired_version: str
) -> tuple[str, str]:
    next_version = ""
    error = ""
    try:
        next_version = vutils.next_version(desired_version, original_version)
    except ValueError:
        next_version = ""
        error = "Invalid version."
    else:
        if not utils.valid_next_version(settings, next_version):
            error = f"The version {next_version} already exists as a tag in Git"
            next_version = ""
    return next_version, error


def resolve_skipped_version(
    settings: t.RepositorySettings, original_version: str, desired_version: str
) -> str:
    """Resolve and validate the next version when the ``version`` step is skipped.

    Mirrors the non-interactive resolution of :func:`step_next_version` so a
    restart that skips the version step still validates the supplied version,
    rejecting invalid values and versions already tagged in Git.

    :param settings: repository settings.
    :param original_version: current version of the repository.
    :param desired_version: version supplied on the command line.
    :returns: the validated next version.
    :raises ValueError: if no version was supplied or it is invalid.
    """
    if not desired_version:
        raise ValueError(
            "A concrete version is required when restarting past the 'version' step."
        )
    next_version, error = _get_next_version(settings, original_version, desired_version)
    if error:
        raise ValueError(error)
    return next_version


def _prompt_version_semver(original_version: str, state: t.PipelineState) -> str:
    """Prompt the user for the next version."""
    prompt_message = "\n   [bold]Select the next version[/bold]"
    options = utils.options_next_version(original_version)
    answer = dutils.choice(prompt_message, options)
    return answer


def step_next_version(
    step_id: str,
    title: str,
    settings: t.RepositorySettings,
    state: t.PipelineState,
    **kwargs: Any,
) -> bool:
    prompted: bool = False
    version_format = state.version_format
    original_version = state.original_version
    desired_version = state.next_version
    if version_format == "calver" and not desired_version:
        # If the version format is calver,
        # we compute the next version
        desired_version = version_format
    elif not desired_version:
        # Prompt the user for the next version if it was not provided as an argument
        desired_version = _prompt_version_semver(original_version, state)
        prompted = True

    next_version, error = _get_next_version(settings, original_version, desired_version)
    if error:
        # If there was an error computing the next version, display it
        # and return False
        dutils.print(error)
        status = False
    elif not prompted:
        next_version = next_version or state.next_version
        # Confirm the version if it was not prompted
        dutils.indented_print(
            f"- Bump version from {settings.version} to {next_version}"
        )
        status = dutils.check_confirm()
    else:
        status = True
    # Update the state with the next version
    state.next_version = next_version if status else state.next_version
    return status
