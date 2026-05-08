from pathlib import Path
from repoplone.release import _types as t
from repoplone.release.steps.local_step import local_step
from types import SimpleNamespace

import pytest
import sys
import textwrap


@pytest.fixture
def fake_settings(tmp_path: Path):
    return SimpleNamespace(root_path=tmp_path)


@pytest.fixture
def fake_state():
    return t.PipelineState(next_version="1.2.3", original_version="1.2.2")


@pytest.fixture(autouse=True)
def _restore_sys_path():
    original = list(sys.path)
    yield
    sys.path[:] = original
    for mod_name in list(sys.modules):
        if mod_name.startswith("repoplone_test_local_step_"):
            del sys.modules[mod_name]


def _write_module(root: Path, name: str, body: str) -> None:
    (root / f"{name}.py").write_text(textwrap.dedent(body))


def test_local_step_resolves_and_invokes_callable(fake_settings, fake_state, tmp_path):
    _write_module(
        tmp_path,
        "repoplone_test_local_step_simple",
        """
        def hook(step_id, title, settings, state, **kwargs):
            assert step_id == "notify"
            assert title == "Notify hook"
            assert state.next_version == "1.2.3"
            assert kwargs == {}
            return True
        """,
    )
    result = local_step(
        step_id="notify",
        title="Notify hook",
        settings=fake_settings,
        state=fake_state,
        entrypoint="repoplone_test_local_step_simple:hook",
    )
    assert result is True


def test_local_step_forwards_extra_kwargs(fake_settings, fake_state, tmp_path):
    _write_module(
        tmp_path,
        "repoplone_test_local_step_kwargs",
        """
        def hook(step_id, title, settings, state, **kwargs):
            assert kwargs == {"channel": "#releases", "ping": "@here"}
            return True
        """,
    )
    assert local_step(
        step_id="notify",
        title="Notify",
        settings=fake_settings,
        state=fake_state,
        entrypoint="repoplone_test_local_step_kwargs:hook",
        channel="#releases",
        ping="@here",
    )


def test_local_step_propagates_false_return(fake_settings, fake_state, tmp_path):
    _write_module(
        tmp_path,
        "repoplone_test_local_step_false",
        """
        def hook(step_id, title, settings, state, **kwargs):
            return False
        """,
    )
    assert (
        local_step(
            step_id="notify",
            title="Notify",
            settings=fake_settings,
            state=fake_state,
            entrypoint="repoplone_test_local_step_false:hook",
        )
        is False
    )


def test_local_step_sys_path_is_idempotent(fake_settings, fake_state, tmp_path):
    _write_module(
        tmp_path,
        "repoplone_test_local_step_idempotent",
        """
        def hook(step_id, title, settings, state, **kwargs):
            return True
        """,
    )
    for _ in range(3):
        local_step(
            step_id="notify",
            title="Notify",
            settings=fake_settings,
            state=fake_state,
            entrypoint="repoplone_test_local_step_idempotent:hook",
        )
    assert sys.path.count(str(tmp_path)) == 1


@pytest.mark.parametrize(
    "entrypoint",
    ["", "no_colon_here", ":missing_module", "missing_callable:", ":"],
)
def test_local_step_rejects_malformed_entrypoint(fake_settings, fake_state, entrypoint):
    with pytest.raises(ValueError):
        local_step(
            step_id="notify",
            title="Notify",
            settings=fake_settings,
            state=fake_state,
            entrypoint=entrypoint,
        )


def test_local_step_rejects_missing_entrypoint(fake_settings, fake_state):
    with pytest.raises(ValueError):
        local_step(
            step_id="notify",
            title="Notify",
            settings=fake_settings,
            state=fake_state,
        )


def test_local_step_raises_on_unknown_module(fake_settings, fake_state):
    with pytest.raises(ImportError):
        local_step(
            step_id="notify",
            title="Notify",
            settings=fake_settings,
            state=fake_state,
            entrypoint="repoplone_test_local_step_does_not_exist:hook",
        )


def test_local_step_raises_on_missing_callable(fake_settings, fake_state, tmp_path):
    _write_module(
        tmp_path,
        "repoplone_test_local_step_missing_attr",
        """
        def other_name(step_id, title, settings, state, **kwargs):
            return True
        """,
    )
    with pytest.raises(AttributeError):
        local_step(
            step_id="notify",
            title="Notify",
            settings=fake_settings,
            state=fake_state,
            entrypoint="repoplone_test_local_step_missing_attr:hook",
        )


def test_local_step_raises_on_non_callable_attr(fake_settings, fake_state, tmp_path):
    _write_module(
        tmp_path,
        "repoplone_test_local_step_not_callable",
        """
        hook = "not a function"
        """,
    )
    with pytest.raises(TypeError):
        local_step(
            step_id="notify",
            title="Notify",
            settings=fake_settings,
            state=fake_state,
            entrypoint="repoplone_test_local_step_not_callable:hook",
        )
