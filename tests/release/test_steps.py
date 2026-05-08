from repoplone.release import _types as t
from repoplone.release import steps


EXPECTED_BUILTIN_IDS = {
    "changelog",
    "version",
    "repository",
    "release_backend",
    "release_frontend",
    "git",
    "gh_release",
    "bye",
    "local_step",
}

EXPECTED_DEFAULT_IDS = EXPECTED_BUILTIN_IDS - {"local_step"}


def test_builtin_steps_contains_expected_ids():
    assert set(steps.BUILTIN_STEPS) == EXPECTED_BUILTIN_IDS


def test_default_steps_excludes_local_step():
    assert set(steps.DEFAULT_STEPS) == EXPECTED_DEFAULT_IDS
    assert "local_step" not in steps.DEFAULT_STEPS


def test_local_step_is_registered_builtin():
    assert "local_step" in steps.BUILTIN_STEPS
    assert callable(steps.BUILTIN_STEPS["local_step"].func)


def test_default_steps_preserves_order():
    assert steps.DEFAULT_STEPS == (
        "changelog",
        "version",
        "repository",
        "release_backend",
        "release_frontend",
        "git",
        "gh_release",
        "bye",
    )


def test_get_steps_returns_release_steps_in_default_order():
    result = steps.get_steps()
    assert [s.id for s in result] == list(steps.DEFAULT_STEPS)
    for step in result:
        assert isinstance(step, t.PipelineReleaseStep)
        assert step.title
        assert callable(step.func)
        assert step.kwargs == {}


def test_builtin_step_titles_match_registry_defaults():
    pipeline_steps = steps.get_steps()
    titles_from_pipeline = {s.id: s.title for s in pipeline_steps}
    titles_from_registry = {
        sid: steps.BUILTIN_STEPS[sid].title for sid in steps.DEFAULT_STEPS
    }
    assert titles_from_pipeline == titles_from_registry
