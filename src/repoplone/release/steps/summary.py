from repoplone.release import _types as t
from repoplone.utils import display as dutils


def step_summary(
    step_id: str, title: str, settings: t.RepositorySettings, state: t.PipelineState
) -> bool:
    dutils.indented_print(
        f"- Completed the release of version {state.next_version}"
        f" from version {state.original_version}"
    )
    return dutils.check_confirm()
