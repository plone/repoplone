from repoplone.release import _types as t
from repoplone.utils import _git as gitutils
from repoplone.utils import display as dutils


def step_update_git(
    step_id: str, title: str, settings: t.RepositorySettings, state: t.PipelineState
) -> bool:
    if not state.dry_run:
        repo = gitutils.repo_for_project(settings.root_path)
        gitutils.finish_release(repo, state.next_version)
        dutils.indented_print(f"- Created tag {state.next_version}")
    else:
        dutils.indented_print(f"- Skipped creating tag {state.next_version}")
    return True
