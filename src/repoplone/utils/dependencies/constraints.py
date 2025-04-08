from .pyproject import get_remote_uv_dependencies
from .versions import package_versions
from mxdev.processing import resolve_dependencies
from packaging.requirements import Requirement
from repoplone import _types as t


PACKAGE_CONSTRAINTS = {
    "plone": {
        "type": "pip",
        "url": "https://dist.plone.org/release/{version}/constraints.txt",
    },
    "Products.CMFPlone": {
        "type": "pip",
        "url": "https://dist.plone.org/release/{version}/constraints.txt",
    },
    "kitconcept.intranet": {
        "type": "uv",
        "url": "https://raw.githubusercontent.com/kitconcept/kitconcept.intranet/refs/tags/{version}/backend/pyproject.toml",
    },
    "portalbrasil.core": {
        "type": "uv",
        "url": "https://raw.githubusercontent.com/portal-br/core/refs/tags/{version}/backend/pyproject.toml",
    },
}


def _get_uv_constraints(url: str, package_name: str, version: str) -> list[str]:
    """Parse constraints inside a remote pyproject.toml file."""
    dependencies, constraints = get_remote_uv_dependencies(url)
    constraints.append(f"{package_name}=={version}")
    return parse_constraints(constraints, dependencies)


def _process_constraint(src: str) -> tuple[str, str]:
    req = Requirement(src)
    return req.name, str(req)


def parse_constraints(lines: list[str], existing: list[str]) -> list[str]:
    constraints = []
    existing_ = dict([_process_constraint(line) for line in existing])
    for line in lines:
        line = line.strip()
        if line.startswith("#") or not line:
            continue
        req_name, _ = _process_constraint(line)
        constraints.append(existing_.pop(req_name, line))
    if existing_:
        constraints.extend(existing_.values())
    return sorted(constraints, key=lambda x: x.lower())


def get_base_constraints(package_name: str, version: str) -> list[str]:
    pkg_config = PACKAGE_CONSTRAINTS.get(package_name)
    if not pkg_config:
        raise AttributeError(f"{package_name} is not supported at the moment.")
    constraints_type = pkg_config["type"]
    constraints_url = pkg_config["url"].format(version=version)
    match constraints_type:
        case "pip":
            _, constraints = resolve_dependencies(constraints_url, [], [], [], "c")
        case "uv":
            constraints = _get_uv_constraints(constraints_url, package_name, version)
        case _:
            raise AttributeError(
                f"{package_name} has an invalid constraints type: {constraints_type}."
            )
    return constraints


def get_package_constraints(
    package_name: str, version: str, existing_pins: t.Requirements
) -> list[str]:
    """Return plone constraints for a version."""
    versions = package_versions(package_name)
    existing_constraints = [
        str(v) for k, v in existing_pins.items() if k != package_name
    ]
    if version not in versions:
        raise RuntimeError(f"{package_name} {version} not available.")

    constraints = get_base_constraints(package_name, version)
    return parse_constraints(constraints, existing_constraints)
