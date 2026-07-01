from repoplone.release import _types as t
from repoplone.release import pipeline

import pytest


PIPELINE_PARAMS = (
    (True, ""),
    (True, "a"),
    (True, "b"),
    (False, "1.0.0"),
)


@pytest.mark.parametrize("dry_run,desired_version", PIPELINE_PARAMS)
def test_pipeline_creation(settings, dry_run: bool, desired_version: str):
    """Test that the pipeline can be created."""
    p = pipeline.ReleasePipeline(
        settings=settings, dry_run=dry_run, desired_version=desired_version
    )
    assert isinstance(p, pipeline.ReleasePipeline)
    assert len(p.steps) == 8


@pytest.mark.parametrize("dry_run,desired_version", PIPELINE_PARAMS)
def test_pipeline_state(settings, dry_run: bool, desired_version: str):
    """Test that the pipeline state is initialized correctly."""
    p = pipeline.ReleasePipeline(
        settings=settings, dry_run=dry_run, desired_version=desired_version
    )
    state = p.state
    assert isinstance(state, t.PipelineState)
    assert state.dry_run == dry_run
    assert state.next_version == desired_version
    assert state.version_format == settings.version_format
    assert state.steps_current == 0
    assert state.steps_total == 8


STEP_IDS = [
    "changelog",
    "version",
    "repository",
    "release_backend",
    "release_frontend",
    "git",
    "gh_release",
    "bye",
]


def _step(step_id: str) -> t.PipelineReleaseStep:
    return t.PipelineReleaseStep(id=step_id, title=step_id, func=lambda *a, **k: True)


def _recording_steps(
    steps: list[t.PipelineReleaseStep], calls: list[str]
) -> list[t.PipelineReleaseStep]:
    """Clone ``steps`` replacing each func with one that records its id."""

    def make(step_id: str):
        def func(sid, title, settings, state, **kwargs):
            calls.append(sid)
            return True

        return func

    return [
        t.PipelineReleaseStep(id=s.id, title=s.title, func=make(s.id)) for s in steps
    ]


def test_resolve_start_empty_returns_zero():
    assert pipeline.resolve_start([_step(i) for i in STEP_IDS], "") == 0


@pytest.mark.parametrize(
    "start_step,expected", [("changelog", 0), ("version", 1), ("git", 5), ("bye", 7)]
)
def test_resolve_start_returns_index(start_step: str, expected: int):
    assert pipeline.resolve_start([_step(i) for i in STEP_IDS], start_step) == expected


def test_resolve_start_unknown_raises():
    steps = [_step(i) for i in STEP_IDS]
    with pytest.raises(ValueError, match="Unknown start step 'nope'"):
        pipeline.resolve_start(steps, "nope")
    # The error lists the valid ids to guide the user.
    with pytest.raises(ValueError, match="changelog"):
        pipeline.resolve_start(steps, "nope")


def test_pipeline_skips_steps_before_start(settings, monkeypatch):
    """Steps before ``start_step`` are skipped but the pipeline still succeeds."""
    captured: list[str] = []
    monkeypatch.setattr(
        pipeline.dutils, "print", lambda *a, **k: captured.append(a[0] if a else "")
    )
    p = pipeline.ReleasePipeline(settings=settings, start_step="version")
    calls: list[str] = []
    p.steps = _recording_steps(p.steps, calls)

    assert p() is True
    assert "changelog" not in calls
    assert calls == STEP_IDS[1:]
    # steps_total stays the full pipeline length; skipped step is marked as such.
    assert p.state.steps_total == 8
    skipped = [line for line in captured if "(skipped)" in line]
    assert len(skipped) == 1
    assert "Display Changelog" in skipped[0]


def test_pipeline_skips_version_with_supplied_version(settings, monkeypatch):
    """Restarting past ``version`` resolves the supplied version in its place."""
    monkeypatch.setattr(
        "repoplone.release.steps.version.vutils.next_version",
        lambda desired, current: "1.0.0a1",
    )
    monkeypatch.setattr(
        "repoplone.release.steps.version.utils.valid_next_version",
        lambda settings, version: True,
    )
    monkeypatch.setattr(pipeline.dutils, "print", lambda *a, **k: None)

    p = pipeline.ReleasePipeline(
        settings=settings, desired_version="1.0.0a1", start_step="git"
    )
    assert p.state.next_version == "1.0.0a1"

    calls: list[str] = []
    p.steps = _recording_steps(p.steps, calls)
    assert p() is True
    assert calls == ["git", "gh_release", "bye"]


def test_pipeline_skip_version_requires_version(settings):
    """Skipping ``version`` without a concrete version is rejected."""
    with pytest.raises(ValueError, match="concrete version"):
        pipeline.ReleasePipeline(settings=settings, start_step="git")


def test_process_steps_returns_all_when_both_enabled(settings):
    """With backend and frontend enabled every configured step is returned."""
    steps = pipeline.process_steps(settings)
    assert [step.id for step in steps] == STEP_IDS


def test_process_steps_drops_backend_when_disabled(settings):
    """A disabled backend excludes the ``release_backend`` step."""
    settings.backend.enabled = False
    ids = [step.id for step in pipeline.process_steps(settings)]
    assert "release_backend" not in ids
    assert "release_frontend" in ids


def test_process_steps_drops_frontend_when_disabled(settings):
    """A disabled frontend excludes the ``release_frontend`` step."""
    settings.frontend.enabled = False
    ids = [step.id for step in pipeline.process_steps(settings)]
    assert "release_frontend" not in ids
    assert "release_backend" in ids


def test_process_desired_version_maps_next_to_empty(settings):
    """The ``next`` sentinel is normalised to an empty string."""
    assert pipeline.process_desired_version(settings, pipeline.NO_VERSION, set()) == ""


def test_process_desired_version_kept_when_version_not_skipped(settings):
    """When the ``version`` step runs the supplied version is returned as-is."""
    assert pipeline.process_desired_version(settings, "1.0.0", set()) == "1.0.0"


def test_process_desired_version_resolves_when_skipped(settings, monkeypatch):
    """Skipping ``version`` with a new version defers to ``resolve_skipped_version``."""
    monkeypatch.setattr(
        pipeline, "resolve_skipped_version", lambda *a, **k: "resolved-version"
    )
    result = pipeline.process_desired_version(settings, "1.0.0a5", {"version"})
    assert result == "resolved-version"


def test_process_desired_version_skips_resolution_when_version_unchanged(
    settings, monkeypatch
):
    """Restarting past ``version`` with the current version skips re-resolution.

    Regression test for #81: on a restart the repository version is already the
    target version, so passing it again must not run ``resolve_skipped_version``
    (which would reject it as an already-existing tag).
    """

    def _boom(*args, **kwargs):
        raise AssertionError("resolve_skipped_version must not be called")

    monkeypatch.setattr(pipeline, "resolve_skipped_version", _boom)
    result = pipeline.process_desired_version(settings, settings.version, {"version"})
    assert result == settings.version
