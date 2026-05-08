from pathlib import Path
from repoplone.release import _types as t
from typing import Any

import importlib
import sys


def _ensure_root_in_path(root: Path) -> None:
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def _resolve_entrypoint(entrypoint: str, root: Path) -> t.PipelineReleaseStepFunction:
    """Resolve a ``module:callable`` entrypoint relative to ``root``.

    :param entrypoint: dotted-path entrypoint in the form ``module.path:callable``.
    :param root: project root added to ``sys.path`` before importing.
    :returns: the resolved callable.
    :raises ValueError: if ``entrypoint`` is empty or missing the ``:`` separator.
    :raises ImportError: if the module cannot be imported.
    :raises AttributeError: if the callable is not found in the module.
    :raises TypeError: if the resolved attribute is not callable.
    """
    if not entrypoint:
        raise ValueError("local_step requires a non-empty `entrypoint` kwarg")
    if ":" not in entrypoint:
        raise ValueError(
            f"local_step entrypoint {entrypoint!r} must be of the form "
            "'module.path:callable'"
        )
    module_name, _, callable_name = entrypoint.partition(":")
    if not module_name or not callable_name:
        raise ValueError(
            f"local_step entrypoint {entrypoint!r} must be of the form "
            "'module.path:callable'"
        )
    _ensure_root_in_path(root)
    module = importlib.import_module(module_name)
    func = getattr(module, callable_name)
    if not callable(func):
        raise TypeError(
            f"local_step entrypoint {entrypoint!r} resolved to a non-callable "
            f"{type(func).__name__}"
        )
    return func


def local_step(
    step_id: str,
    title: str,
    settings: t.RepositorySettings,
    state: t.PipelineState,
    **kwargs: Any,
) -> bool:
    """Resolve and invoke a project-local callable as a release step.

    The callable is loaded from a module living under ``settings.root_path``.
    The project root is added to ``sys.path`` (idempotently) before the
    import is attempted, so a project running ``uvx repoplone`` from its
    root can expose hooks under e.g. ``scripts/repoplone_hooks.py`` and
    reference them as ``scripts.repoplone_hooks:my_hook``.

    :param step_id: identifier under which this step was registered.
    :param title: human-readable title shown by the pipeline.
    :param settings: repository settings.
    :param state: pipeline state for the current release run.
    :param kwargs: must contain ``entrypoint`` (``module.path:callable``).
        Any remaining kwargs are forwarded to the resolved callable.
    :returns: the boolean return value of the resolved callable.
    :raises ValueError: if ``entrypoint`` is missing or malformed.
    :raises ImportError: if the entrypoint module cannot be imported.
    :raises AttributeError: if the entrypoint callable is not found.
    :raises TypeError: if the resolved attribute is not callable.
    """
    extra: dict[str, Any] = dict(kwargs)
    entrypoint: str = extra.pop("entrypoint", "")
    func = _resolve_entrypoint(entrypoint, settings.root_path)
    return func(step_id, title, settings, state, **extra)
