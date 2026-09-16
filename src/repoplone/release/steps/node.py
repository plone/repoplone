from repoplone import _types as rt
from repoplone.release import _types as t
from repoplone.utils import display as dutils
from repoplone.utils import release as utils
from repoplone.utils import versions as vutils
from typing import Any


def step_release_node(
    step_id: str,
    title: str,
    settings: t.RepositorySettings,
    state: t.PipelineState,
    **kwargs: Any,
) -> bool:
    """Release every package of the node family, in document order."""
    packages = [
        package for package in settings.packages_for(rt.FAMILY_NODE) if package.enabled
    ]
    if not packages:
        dutils.indented_print("- No Node package to release")
        return True
    next_version = vutils.convert_python_node_version(state.next_version)
    for package in packages:
        utils.release_frontend(settings, package, next_version, state.dry_run)
        dutils.indented_print(f"- Released {package.name}: {next_version}")
    return True
