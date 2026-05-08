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
}


def test_builtin_steps_contains_expected_ids():
    assert set(steps.BUILTIN_STEPS) == EXPECTED_BUILTIN_IDS


def test_default_steps_matches_registry():
    assert set(steps.DEFAULT_STEPS) == set(steps.BUILTIN_STEPS)


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
    titles_from_registry = {sid: b.title for sid, b in steps.BUILTIN_STEPS.items()}
    assert titles_from_pipeline == titles_from_registry
