from .constraints import get_package_constraints
from .frontend import update_base_package as update_frontend_base_package
from .pyproject import current_base_package
from .pyproject import get_all_pinned_dependencies
from .pyproject import parse_pyproject
from .pyproject import update_pyproject
from .versions import check_backend_base_package
from .versions import check_frontend_base_package
from .versions import node_latest_package_version
from .versions import python_latest_package_version
from pathlib import Path


def update_backend_constraints(
    pyproject_path: Path, package_name: str, version: str
) -> bool:
    """Update constraints for a base package in pyproject.toml."""
    if pyproject := parse_pyproject(pyproject_path):
        existing_pins = get_all_pinned_dependencies(pyproject)
        constraints = get_package_constraints(package_name, version, existing_pins)
        update_pyproject(pyproject_path, package_name, version, constraints)
        return True
    return False


__all__ = [
    "check_backend_base_package",
    "check_frontend_base_package",
    "current_base_package",
    "get_all_pinned_dependencies",
    "get_package_constraints",
    "node_latest_package_version",
    "parse_pyproject",
    "python_latest_package_version",
    "update_backend_constraints",
    "update_frontend_base_package",
    "update_pyproject",
]
