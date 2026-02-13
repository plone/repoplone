from packaging.requirements import Requirement
from pathlib import Path
from repoplone import _types as t
from repoplone.utils._requests import get_remote_data
from tomlkit import container
from tomlkit import items

import re
import tomlkit


PLONE_VERSION_PATTERN = re.compile(r"^Framework :: Plone :: (\d+\.\d+)$")
PYTHON_VERSION_PATTERN = re.compile(r"^Programming Language :: Python :: (\d+\.\d+)$")


def _process_requirements(data: tomlkit.TOMLDocument, key: str) -> list[Requirement]:
    requirements: list[Requirement] = []
    raw_dependencies: items.Table | items.Array = (
        _get_project_table(data).get(key.split(".")[-1])
        if key.startswith("project")
        else data.get(key)
    ) or tomlkit.table()
    if isinstance(raw_dependencies, items.Array):
        tmp_table = tomlkit.table()
        tmp_table.add(key, raw_dependencies)
        raw_dependencies = tmp_table
    if raw_dependencies:
        for group_values in raw_dependencies.values():
            for value in group_values:
                requirements.append(Requirement(value))
    return requirements


def _get_project_table(data: tomlkit.TOMLDocument) -> items.Table:
    """Return the current project information."""
    project = data["project"]
    if not isinstance(project, items.Table | container.OutOfOrderTableProxy):
        raise ValueError("Invalid data")
    return project


def _get_uv_table(data: tomlkit.TOMLDocument) -> items.Table:
    """Return the current project information."""
    tool: items.Table | None = data.get("tool")
    uv_config: items.Table | None = tool.get("uv") if tool else None
    if not uv_config:
        uv_config = tomlkit.table()
    return uv_config


def _get_project_dependencies(data: tomlkit.TOMLDocument) -> t.Requirements:
    """Return the current project dependencies."""
    raw_dependencies = _process_requirements(data, "project.dependencies")
    dependencies: t.Requirements = {req.name: req for req in raw_dependencies}
    return dependencies


def get_all_pinned_dependencies(data: tomlkit.TOMLDocument) -> t.Requirements:
    """Return dependencies that have a pinned version in pyproject.toml."""
    raw_dependencies: list[Requirement] = []
    for key in (
        "project.dependencies",
        "project.optional-dependencies",
        "dependency-groups",
    ):
        raw_dependencies.extend(_process_requirements(data, key))
    dependencies: t.Requirements = {
        req.name: req for req in raw_dependencies if req.specifier != ""
    }
    return dependencies


def get_remote_uv_dependencies(url: str) -> tuple[list[str], list[str]]:
    """Return dependencies listed under [tool.uv]."""
    response = get_remote_data(url)
    data = response.content.decode("utf-8")
    pyproject = _parse_pyproject(data)
    dependencies = [
        str(req)
        for req in _process_requirements(pyproject, "project.dependencies")
        if req.specifier != ""
    ]
    uv_config = _get_uv_table(pyproject)
    constraints = list(uv_config.get("constraint-dependencies") or tomlkit.array())
    return dependencies, constraints


def managed_by_uv(pyproject: Path) -> bool:
    """Check if a package is managed by UV.

    ```toml
    [tool.uv]
    managed = false
    ```
    """
    data = tomlkit.parse(pyproject.read_text())
    uv_config = _get_uv_table(data)
    is_managed = uv_config.get("managed", True)
    return is_managed


def current_base_package(pyproject: Path, package_name: str) -> str | None:
    """Return the current base package version."""
    data = tomlkit.parse(pyproject.read_text())
    deps: t.Requirements = _get_project_dependencies(data)
    req = deps.get(package_name)
    if req:
        return str(req.specifier)[2:]
    return None


def _update_dependency(data: tomlkit.TOMLDocument, package: str, version: str) -> None:
    project = _get_project_table(data)
    deps = tomlkit.array()
    deps.multiline(True)
    project_dependencies = _get_project_dependencies(data)
    for dep_name in project_dependencies:
        if re.match(f"^{package}$", dep_name):
            dep = f"{package}=={version}"
        else:
            # Keep dependency as stated before
            dep = str(project_dependencies[dep_name])
        deps.append(dep)
    project.update({"dependencies": deps})


def _update_constraints(data: tomlkit.TOMLDocument, raw_constraints: list[str]) -> None:
    tool_uv = data.get("tool", {}).get("uv", {})
    if not tool_uv:
        tool_uv = tomlkit.table(False)
        data.append("tool.uv", tool_uv)
    constraints = tomlkit.array()
    constraints.multiline(True)
    for line in raw_constraints:
        item = tomlkit.item(line)
        constraints.append(item)
    tool_uv.update({"constraint-dependencies": constraints})


def _update_classifiers(
    data: tomlkit.TOMLDocument, python_versions: list[str], plone_versions: list[str]
) -> None:
    project = _get_project_table(data)
    classifiers: list[str] = project.get("classifiers", [])
    # Remove existing Python and Plone version classifiers
    for classifier in classifiers:
        if PYTHON_VERSION_PATTERN.match(classifier) or PLONE_VERSION_PATTERN.match(
            classifier
        ):
            classifiers.remove(classifier)
    # Add updated Python version classifiers
    for version in python_versions:
        classifiers.append(f"Programming Language :: Python :: {version}")
    # Add updated Plone version classifiers
    for version in plone_versions:
        classifiers.append(f"Framework :: Plone :: {version}")
    classifiers.sort()
    # Update project classifiers
    project.update({"classifiers": classifiers})


def _parse_pyproject(src: str) -> tomlkit.TOMLDocument:
    return tomlkit.parse(src)


def parse_pyproject(pyproject: Path) -> tomlkit.TOMLDocument:
    return _parse_pyproject(pyproject.read_text())


def _parse_classifiers(data: tomlkit.TOMLDocument, pattern: re.Pattern) -> list[str]:
    """Parse classifiers matching the given pattern and return the captured groups."""
    project = _get_project_table(data)
    classifiers = project.get("classifiers", [])
    result = []
    for classifier in classifiers:
        match = pattern.match(classifier)
        if match:
            result.append(match.group(1))
    return result


def python_versions(data: tomlkit.TOMLDocument) -> list[str]:
    """Return the supported Python versions from classifiers."""
    versions = _parse_classifiers(data, PYTHON_VERSION_PATTERN)
    return versions


def plone_versions(data: tomlkit.TOMLDocument) -> list[str]:
    """Return the supported Plone versions from classifiers."""
    versions = _parse_classifiers(data, PLONE_VERSION_PATTERN)
    return versions


def update_pyproject(
    pyproject: Path,
    package_name: str,
    version: str,
    constraints: list[str],
    python_versions: list[str] | None = None,
    plone_versions: list[str] | None = None,
):
    """Update pyproject.toml with a new version of the package."""
    data: tomlkit.TOMLDocument = tomlkit.parse(pyproject.read_text())
    # Update dependency
    _update_dependency(data, package_name, version)
    # Constraints
    _update_constraints(data, constraints)
    # Update classifiers if Python and Plone versions are provided
    if python_versions and plone_versions:
        _update_classifiers(data, python_versions, plone_versions)
    # Update pyproject
    pyproject.write_text(tomlkit.dumps(data))
