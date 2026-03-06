from repoplone.release import _types as t
from repoplone.utils import display as dutils
from repoplone.utils import release as utils


def step_release_backend(
    step_id: str, title: str, settings: t.RepositorySettings, state: t.PipelineState
) -> bool:
    if settings.backend.enabled:
        utils.release_backend(settings, state.next_version, state.dry_run)
        dutils.indented_print(
            f"- Released {settings.backend.name}: {state.next_version}"
        )
    else:
        dutils.indented_print("- Backend packaged is disabled")
    return True
