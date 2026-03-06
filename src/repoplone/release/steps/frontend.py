from repoplone.release import _types as t
from repoplone.utils import display as dutils
from repoplone.utils import release as utils
from repoplone.utils import versions as vutils


def step_release_frontend(
    step_id: str, title: str, settings: t.RepositorySettings, state: t.PipelineState
) -> bool:
    if settings.frontend.enabled:
        next_version = vutils.convert_python_node_version(state.next_version)
        utils.release_frontend(settings, next_version, state.dry_run)
        dutils.indented_print(f"- Released {settings.frontend.name}: {next_version}")
    else:
        dutils.indented_print("- Frontend packaged is disabled")
    return True
