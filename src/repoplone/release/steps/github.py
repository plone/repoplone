from repoplone.release import _types as t
from repoplone.utils import _github as ghutils
from repoplone.utils import display as dutils


def step_gh_release(
    step_id: str, title: str, settings: t.RepositorySettings, state: t.PipelineState
) -> bool:
    if state.dry_run:
        dutils.indented_print("- Skipping GitHub release creation")
        return True
    try:
        check_token = ghutils.check_token(settings)
    except ValueError:
        dutils.indented_print(
            "- Skipping GitHub release creation as this is not a valid repository."
        )
        return False
    if check_token:
        msg = ghutils.create_release(
            settings, state.original_version, state.next_version
        )
        dutils.indented_print(msg)
    else:
        dutils.indented_print(
            "- Skipping GitHub release creation as you do not have a GITHUB_TOKEN"
            "environment variable set"
        )
    return True
