from repoplone.release.config import RepositoryConfigError
from repoplone.release.config import build_release_steps
from repoplone.release.steps import BUILTIN_STEPS
from repoplone.release.steps import DEFAULT_STEPS

import pytest


def test_no_config_returns_default_pipeline():
    result = build_release_steps(None)
    assert [s.id for s in result] == list(DEFAULT_STEPS)


def test_empty_config_returns_default_pipeline():
    result = build_release_steps({})
    assert [s.id for s in result] == list(DEFAULT_STEPS)


def test_section_without_steps_returns_default_pipeline():
    result = build_release_steps({"registry": {}})
    assert [s.id for s in result] == list(DEFAULT_STEPS)


def test_custom_order_using_only_builtins():
    config = {
        "steps": ["version", "changelog", "git", "bye"],
    }
    result = build_release_steps(config)
    assert [s.id for s in result] == ["version", "changelog", "git", "bye"]
    for step in result:
        assert step.title == BUILTIN_STEPS[step.id].title
        assert step.kwargs == {}


def test_subset_of_builtins_omits_others():
    config = {"steps": ["changelog", "version", "bye"]}
    result = build_release_steps(config)
    ids = [s.id for s in result]
    assert ids == ["changelog", "version", "bye"]
    assert "gh_release" not in ids


def test_registry_entry_resolves_to_local_step():
    config = {
        "steps": ["changelog", "notify_slack", "bye"],
        "registry": {
            "notify_slack": {
                "title": "Notify internal Slack",
                "function": "local_step",
                "args": {"entrypoint": "scripts.notify:hook", "channel": "#releases"},
            }
        },
    }
    result = build_release_steps(config)
    notify = next(s for s in result if s.id == "notify_slack")
    assert notify.title == "Notify internal Slack"
    assert notify.func is BUILTIN_STEPS["local_step"].func
    assert notify.kwargs == {
        "entrypoint": "scripts.notify:hook",
        "channel": "#releases",
    }


def test_registry_entry_default_title_falls_back_to_builtin():
    config = {
        "steps": ["custom"],
        "registry": {
            "custom": {
                "function": "local_step",
                "args": {"entrypoint": "scripts.x:hook"},
            }
        },
    }
    result = build_release_steps(config)
    assert result[0].title == BUILTIN_STEPS["local_step"].title


def test_unknown_step_id_raises():
    with pytest.raises(RepositoryConfigError, match="unknown id 'nope'"):
        build_release_steps({"steps": ["changelog", "nope"]})


def test_duplicate_step_ids_raise():
    with pytest.raises(RepositoryConfigError, match="duplicate ids"):
        build_release_steps({"steps": ["changelog", "version", "changelog"]})


def test_local_step_in_steps_directly_is_rejected():
    with pytest.raises(RepositoryConfigError, match="cannot reference 'local_step'"):
        build_release_steps({"steps": ["local_step"]})


def test_registry_entry_missing_function_raises():
    with pytest.raises(RepositoryConfigError, match="missing required key 'function'"):
        build_release_steps({"steps": ["foo"], "registry": {"foo": {"title": "Foo"}}})


def test_registry_entry_unknown_function_raises():
    with pytest.raises(RepositoryConfigError, match="not a registered built-in"):
        build_release_steps({
            "steps": ["foo"],
            "registry": {"foo": {"function": "made_up"}},
        })


def test_local_step_registry_entry_without_entrypoint_raises():
    with pytest.raises(RepositoryConfigError, match="entrypoint is required"):
        build_release_steps({
            "steps": ["foo"],
            "registry": {"foo": {"function": "local_step"}},
        })


def test_steps_must_be_list_of_strings():
    with pytest.raises(RepositoryConfigError, match="list of strings"):
        build_release_steps({"steps": [1, 2, 3]})


def test_release_section_must_be_table():
    with pytest.raises(RepositoryConfigError, match="must be a table"):
        build_release_steps("not a table")


def test_registry_section_must_be_table():
    with pytest.raises(
        RepositoryConfigError, match=r"\[repository.release.registry\] must be a table"
    ):
        build_release_steps({"steps": ["changelog"], "registry": "not a table"})


def test_registry_entry_args_must_be_table():
    with pytest.raises(RepositoryConfigError, match="args must be a table"):
        build_release_steps({
            "steps": ["foo"],
            "registry": {
                "foo": {"function": "local_step", "args": "string"},
            },
        })
