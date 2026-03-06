from repoplone.release import _types as t
from repoplone.utils import changelog as chgutils
from repoplone.utils import display as dutils


def step_prepare_changelog(
    step_id: str, title: str, settings: t.RepositorySettings, state: t.PipelineState
) -> bool:
    # Changelog
    ## First display the changelog
    new_entries, _ = chgutils.update_changelog(
        settings, draft=True, version=state.next_version
    )
    settings._tmp_changelog = new_entries
    text = f"{'=' * 50}\n{new_entries}\n{'=' * 50}"
    dutils.indented_print(text)
    return dutils.check_confirm()
