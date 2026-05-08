"""Regression tests for the ``next_version`` step display bug (#62).

Before the fix, ``step_next_version`` showed ``state.next_version`` (the raw
user input — e.g. ``"a"``, ``"minor"``, or ``""`` for calver) in the bump
confirmation prompt instead of the version returned by
``_get_next_version``. These tests capture the displayed text and assert it
contains the resolved version.
"""

from repoplone.release import _types as t
from repoplone.release.steps.version import step_next_version
from types import SimpleNamespace

import pytest


@pytest.fixture
def fake_settings():
    return SimpleNamespace(version="1.0.0b11")


@pytest.fixture
def captured_output(monkeypatch):
    """Mock display + confirmation; return list of indented_print calls."""
    captured: list[str] = []
    monkeypatch.setattr(
        "repoplone.release.steps.version.dutils.indented_print",
        lambda text: captured.append(text),
    )
    monkeypatch.setattr(
        "repoplone.release.steps.version.dutils.check_confirm",
        lambda: True,
    )
    monkeypatch.setattr(
        "repoplone.release.steps.version.dutils.print",
        lambda *args, **kwargs: None,
    )
    return captured


@pytest.fixture
def stub_resolution(monkeypatch):
    """Patch the version-resolution boundary; tests pick the resolved value."""

    def _stub(resolved: str):
        monkeypatch.setattr(
            "repoplone.release.steps.version.vutils.next_version",
            lambda desired, current: resolved,
        )
        monkeypatch.setattr(
            "repoplone.release.steps.version.utils.valid_next_version",
            lambda settings, version: True,
        )

    return _stub


def test_segment_input_shows_resolved_version_in_confirmation(
    fake_settings, captured_output, stub_resolution
):
    stub_resolution("1.0.0a0")
    state = t.PipelineState(
        version_format="semver",
        original_version="1.0.0b11",
        next_version="a",
    )

    ok = step_next_version("version", "Next version", fake_settings, state)

    assert ok is True
    assert any("to 1.0.0a0" in line for line in captured_output), captured_output
    assert not any(line.rstrip().endswith(" to a") for line in captured_output)


def test_calver_empty_input_shows_computed_version_in_confirmation(
    fake_settings, captured_output, stub_resolution
):
    stub_resolution("20260213.1")
    state = t.PipelineState(
        version_format="calver",
        original_version="20260213.0",
        next_version="",
    )

    ok = step_next_version("version", "Next version", fake_settings, state)

    assert ok is True
    assert any("to 20260213.1" in line for line in captured_output), captured_output
    assert not any(line.rstrip().endswith(" to ") for line in captured_output)


def test_state_is_updated_with_resolved_version_after_confirmation(
    fake_settings, captured_output, stub_resolution
):
    stub_resolution("1.0.0a0")
    state = t.PipelineState(
        version_format="semver",
        original_version="1.0.0b11",
        next_version="a",
    )

    step_next_version("version", "Next version", fake_settings, state)

    assert state.next_version == "1.0.0a0"
