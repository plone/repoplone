from repoplone.release import _types as t


# In the future this should be configurable,
# but for now we hardcode the steps here.
CONFIG: tuple[tuple[str, str, str], ...] = (
    (
        "changelog",
        "Display Changelog",
        "repoplone.release.steps.changelog.step_prepare_changelog",
    ),
    (
        "version",
        "Next version",
        "repoplone.release.steps.version.step_next_version",
    ),
    (
        "repository",
        "Update repository components",
        "repoplone.release.steps.repository.step_update_repository",
    ),
    (
        "release_backend",
        "Release backend",
        "repoplone.release.steps.backend.step_release_backend",
    ),
    (
        "release_frontend",
        "Release frontend",
        "repoplone.release.steps.frontend.step_release_frontend",
    ),
    (
        "git",
        "Commit changes, create tag",
        "repoplone.release.steps.git.step_update_git",
    ),
    (
        "gh_release",
        "Create GitHub release",
        "repoplone.release.steps.github.step_gh_release",
    ),
    (
        "bye",
        "Summary and goodbye",
        "repoplone.release.steps.summary.step_summary",
    ),
)


def _get_step_func(path: str) -> t.PipelineReleaseStepFunction:
    """Dynamically import a function from a string path.

    Example path: "repoplone.release.steps.changelog.step_prepare_changelog"
    """
    module_path, func_name = path.rsplit(".", 1)
    module = __import__(module_path, fromlist=[func_name])
    func = getattr(module, func_name)
    return func


def get_steps() -> list[t.PipelineReleaseStep]:
    steps = []
    for step_id, title, func_path in CONFIG:
        try:
            func = _get_step_func(func_path)
        except (ImportError, AttributeError) as e:
            raise ImportError(f"Could not find the step '{func_path}'") from e
        steps.append(t.PipelineReleaseStep(step_id, title, func))
    return steps
