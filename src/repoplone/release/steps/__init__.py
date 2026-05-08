from dataclasses import dataclass
from repoplone.release import _types as t
from repoplone.release.steps.backend import step_release_backend
from repoplone.release.steps.changelog import step_prepare_changelog
from repoplone.release.steps.frontend import step_release_frontend
from repoplone.release.steps.git import step_update_git
from repoplone.release.steps.github import step_gh_release
from repoplone.release.steps.local_step import local_step
from repoplone.release.steps.repository import step_update_repository
from repoplone.release.steps.summary import step_summary
from repoplone.release.steps.version import step_next_version


@dataclass(frozen=True)
class BuiltinStep:
    """A release step function registered as a built-in.

    :param title: default human-readable title shown when no override is provided.
    :param func: the callable executed by the pipeline.
    """

    title: str
    func: t.PipelineReleaseStepFunction


BUILTIN_STEPS: dict[str, BuiltinStep] = {
    "changelog": BuiltinStep("Display Changelog", step_prepare_changelog),
    "version": BuiltinStep("Next version", step_next_version),
    "repository": BuiltinStep("Update repository components", step_update_repository),
    "release_backend": BuiltinStep("Release backend", step_release_backend),
    "release_frontend": BuiltinStep("Release frontend", step_release_frontend),
    "git": BuiltinStep("Commit changes, create tag", step_update_git),
    "gh_release": BuiltinStep("Create GitHub release", step_gh_release),
    "bye": BuiltinStep("Summary and goodbye", step_summary),
    "local_step": BuiltinStep("Run local step", local_step),
}


DEFAULT_STEPS: tuple[str, ...] = (
    "changelog",
    "version",
    "repository",
    "release_backend",
    "release_frontend",
    "git",
    "gh_release",
    "bye",
)


def get_steps() -> list[t.PipelineReleaseStep]:
    """Return the default ordered list of release pipeline steps.

    :returns: list of :class:`PipelineReleaseStep` instances in execution order.
    """
    steps: list[t.PipelineReleaseStep] = []
    for step_id in DEFAULT_STEPS:
        builtin = BUILTIN_STEPS[step_id]
        steps.append(
            t.PipelineReleaseStep(id=step_id, title=builtin.title, func=builtin.func)
        )
    return steps
