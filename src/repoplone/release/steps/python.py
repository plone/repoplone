from repoplone import _types as rt
from repoplone.release import _types as t
from repoplone.utils import display as dutils
from repoplone.utils import release as utils
from typing import Any


def step_release_python(
    step_id: str,
    title: str,
    settings: t.RepositorySettings,
    state: t.PipelineState,
    **kwargs: Any,
) -> bool:
    """Release every package of the python family, in document order."""
    packages = [
        package
        for package in settings.packages_for(rt.FAMILY_PYTHON)
        if package.enabled
    ]
    if not packages:
        dutils.indented_print("- No Python package to release")
        return True
    for package in packages:
        utils.release_backend(settings, package, state.next_version, state.dry_run)
        dutils.indented_print(f"- Released {package.name}: {state.next_version}")
    return True
