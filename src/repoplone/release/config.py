"""Parse the ``[repository.release]`` section of ``repository.toml``."""

from collections.abc import Mapping
from repoplone.release import _types as t
from repoplone.release.steps import BUILTIN_STEPS
from repoplone.release.steps import DEFAULT_STEPS
from typing import Any


class RepositoryConfigError(ValueError):
    """Raised when ``[repository.release]`` is misconfigured."""


def _default_pipeline() -> list[t.PipelineReleaseStep]:
    return [
        t.PipelineReleaseStep(
            id=sid, title=BUILTIN_STEPS[sid].title, func=BUILTIN_STEPS[sid].func
        )
        for sid in DEFAULT_STEPS
    ]


def _validate_registry_entry(
    entry_id: str, entry: Any
) -> tuple[str, str, dict[str, Any]]:
    """Validate a ``[repository.release.registry.<id>]`` entry.

    :param entry_id: id of the registry entry.
    :param entry: dict-like value of the entry.
    :returns: tuple ``(function_id, title, args)`` ready to build a step.
    :raises RepositoryConfigError: on any validation failure.
    """
    if not isinstance(entry, Mapping):
        raise RepositoryConfigError(
            f"[repository.release.registry.{entry_id}] must be a table"
        )
    function_id = entry.get("function")
    if not function_id:
        raise RepositoryConfigError(
            f"[repository.release.registry.{entry_id}] is missing required key "
            "'function'"
        )
    if function_id not in BUILTIN_STEPS:
        known = ", ".join(sorted(BUILTIN_STEPS))
        raise RepositoryConfigError(
            f"[repository.release.registry.{entry_id}].function = {function_id!r} "
            f"is not a registered built-in. Known: {known}"
        )
    args_raw = entry.get("args") or {}
    if not isinstance(args_raw, Mapping):
        raise RepositoryConfigError(
            f"[repository.release.registry.{entry_id}].args must be a table"
        )
    if function_id == "local_step" and not args_raw.get("entrypoint"):
        raise RepositoryConfigError(
            f"[repository.release.registry.{entry_id}].args.entrypoint is required "
            "when function = 'local_step'"
        )
    title = entry.get("title") or BUILTIN_STEPS[function_id].title
    return function_id, str(title), dict(args_raw)


def _find_duplicates(items: list[str]) -> list[str]:
    seen: set[str] = set()
    dups: list[str] = []
    for item in items:
        if item in seen and item not in dups:
            dups.append(item)
        seen.add(item)
    return dups


def _validate_steps_list(steps_raw: Any) -> list[str]:
    if not isinstance(steps_raw, list) or not all(
        isinstance(s, str) for s in steps_raw
    ):
        raise RepositoryConfigError(
            "[repository.release].steps must be a list of strings"
        )
    duplicates = _find_duplicates(list(steps_raw))
    if duplicates:
        raise RepositoryConfigError(
            f"[repository.release].steps contains duplicate ids: {duplicates}"
        )
    return list(steps_raw)


def _validate_registry(registry_raw: Any) -> dict[str, tuple[str, str, dict[str, Any]]]:
    if not isinstance(registry_raw, Mapping):
        raise RepositoryConfigError("[repository.release.registry] must be a table")
    user_specs: dict[str, tuple[str, str, dict[str, Any]]] = {}
    for entry_id, entry in registry_raw.items():
        user_specs[entry_id] = _validate_registry_entry(entry_id, entry)
    return user_specs


def _resolve_step(
    step_id: str,
    user_specs: dict[str, tuple[str, str, dict[str, Any]]],
) -> t.PipelineReleaseStep:
    if step_id in user_specs:
        function_id, title, args = user_specs[step_id]
        builtin = BUILTIN_STEPS[function_id]
        return t.PipelineReleaseStep(
            id=step_id, title=title, func=builtin.func, kwargs=args
        )
    if step_id == "local_step":
        raise RepositoryConfigError(
            "[repository.release].steps cannot reference 'local_step' directly. "
            "Declare a registry entry under [repository.release.registry.<id>] "
            "with function = 'local_step' and args.entrypoint = 'module:callable'."
        )
    if step_id in BUILTIN_STEPS:
        builtin = BUILTIN_STEPS[step_id]
        return t.PipelineReleaseStep(id=step_id, title=builtin.title, func=builtin.func)
    known = sorted(set(BUILTIN_STEPS) | set(user_specs))
    raise RepositoryConfigError(
        f"[repository.release].steps references unknown id {step_id!r}. "
        f"Known: {', '.join(known)}"
    )


def build_release_steps(release_config: Any) -> list[t.PipelineReleaseStep]:
    """Build the ordered list of release pipeline steps.

    Resolves the parsed ``[repository.release]`` section into a list of
    :class:`PipelineReleaseStep` instances. When ``release_config`` is empty
    or has no ``steps`` key, the default pipeline order is returned.

    :param release_config: parsed ``[repository.release]`` mapping, or ``None``.
    :returns: ordered list of :class:`PipelineReleaseStep`.
    :raises RepositoryConfigError: on any validation failure.
    """
    if not release_config:
        return _default_pipeline()
    if not isinstance(release_config, Mapping):
        raise RepositoryConfigError("[repository.release] must be a table")
    steps_raw = release_config.get("steps")
    if not steps_raw:
        return _default_pipeline()
    step_ids = _validate_steps_list(steps_raw)
    user_specs = _validate_registry(release_config.get("registry") or {})
    return [_resolve_step(sid, user_specs) for sid in step_ids]
