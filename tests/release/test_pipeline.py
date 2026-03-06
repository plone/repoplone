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
