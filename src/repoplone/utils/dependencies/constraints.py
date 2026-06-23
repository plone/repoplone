from .pyproject import get_remote_uv_dependencies
from .versions import pypi_package_versions
from mxdev.processing import resolve_dependencies
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from repoplone import _types as t
from repoplone import exceptions
from repoplone.distributions import PACKAGE_CONSTRAINTS


def _get_uv_constraints(url: str, package_name: str, version: str) -> list[str]:
    """Parse constraints from a remote ``pyproject.toml`` managed by uv.

    :param url: Constraints URL already formatted with the requested version.
    :param package_name: Name of the base package.
    :param version: Version to pin, or ``@branch`` to install from a branch.
    :returns: Sorted list of constraint specifiers.
    """
    if from_branch := version.startswith("@"):
        # Fetch the branch's pyproject.toml instead of a tagged release.
        url = url.replace(f"/tags/{version}", f"/heads/{version[1:]}")
    dependencies, constraints = get_remote_uv_dependencies(url)
    if not from_branch:
        # A branch install is pinned via [tool.uv.sources], not a == constraint.
        constraints.append(f"{package_name}=={version}")
    return parse_constraints(constraints, dependencies)


def _get_pip_constraints(url: str, package_name: str, version: str) -> list[str]:
    """Resolve constraints from a remote source using pip.

    :param url: URL of the remote constraints source.
    :param package_name: Name of the base package.
    :param version: Version being resolved.
    :returns: List of constraint specifiers.
    :raises exceptions.RepoPloneExternalException: If fetching or resolution fails.
    """
    try:
        _, constraints = resolve_dependencies(url, [], [], [], "c")
    except Exception as exc:
        raise exceptions.RepoPloneExternalException(
            f"Failed to fetch constraints from {url}: {exc}"
        ) from exc
    return constraints


def _process_constraint(src: str) -> tuple[str, str]:
    """Return the canonical name and normalized form of a constraint line.

    :param src: A single requirement/constraint specifier.
    :returns: Tuple of ``(canonical_name, normalized_requirement)``.
    """
    req = Requirement(src)
    return canonicalize_name(req.name), str(req)


def parse_constraints(lines: list[str], existing: list[str]) -> list[str]:
    """Merge constraint lines with existing pins, preferring the existing ones.

    Comment and blank lines are skipped. When a package appears in both
    ``lines`` and ``existing``, the ``existing`` specifier wins; any leftover
    ``existing`` entries are appended.

    :param lines: Constraint specifiers parsed from the remote source.
    :param existing: Constraint specifiers already present locally.
    :returns: Sorted, de-duplicated list of constraint specifiers.
    """
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
    return sorted(constraints, key=lambda x: canonicalize_name(Requirement(x).name))


def get_constraint_info(package_name: str) -> t.PackageConstraintInfo:
    """Return the constraint configuration for a supported base package.

    :param package_name: Name of the base package.
    :returns: The package's constraint configuration.
    :raises AttributeError: If the package is not supported.
    """
    pkg_config = PACKAGE_CONSTRAINTS.get(package_name)
    if not pkg_config:
        raise AttributeError(f"{package_name} is not supported at the moment.")
    elif warning := pkg_config.get("warning"):
        print(f"Warning: {warning}")
    return pkg_config


def get_base_constraints(package_name: str, version: str) -> list[str]:
    """Return the constraints for a base package at a given version or branch.

    :param package_name: Name of the base package.
    :param version: Version to pin, or ``@branch`` to install from a branch.
    :returns: List of constraint specifiers.
    :raises AttributeError: If the package has an invalid constraints type.
    """
    pkg_config = get_constraint_info(package_name)
    constraints_type = pkg_config["type"]
    constraints_url = pkg_config["url"].format(version=version)
    match constraints_type:
        case "pip":
            constraints = _get_pip_constraints(constraints_url, package_name, version)
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
    """Return package constraints for a version, excluding packages already pinned.

    Packages declared in ``project.dependencies``,
    ``project.optional-dependencies``, ``dependency-groups`` or
    ``tool.uv.override-dependencies`` are skipped so each package appears only
    once in the final ``pyproject.toml``.
    """
    from_branch = version.startswith("@")
    if not from_branch and version not in pypi_package_versions(package_name):
        raise RuntimeError(f"{package_name} {version} not available.")
    excluded = {
        canonicalize_name(name) for name in existing_pins if name != package_name
    }
    constraints = get_base_constraints(package_name, version)
    filtered: list[str] = []
    for line in constraints:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if canonicalize_name(Requirement(stripped).name) in excluded:
            continue
        filtered.append(stripped)
    return sorted(filtered, key=lambda line: canonicalize_name(Requirement(line).name))
