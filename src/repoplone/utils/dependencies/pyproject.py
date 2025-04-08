from packaging.requirements import Requirement
from pathlib import Path
from repoplone import _types as t
from tomlkit import container
from tomlkit import items

import re
import requests
import tomlkit


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
    response = requests.get(url)  # noQA: S113
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
    for dep in _get_project_dependencies(data):
        if re.match(f"^{package}", dep):
            dep = f"{package}=={version}"
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


def _parse_pyproject(src: str) -> tomlkit.TOMLDocument:
    return tomlkit.parse(src)


def parse_pyproject(pyproject: Path) -> tomlkit.TOMLDocument:
    return _parse_pyproject(pyproject.read_text())


def update_pyproject(
    pyproject: Path, package_name: str, version: str, constraints: list[str]
):
    """Update pyproject.toml with a new version of the package."""
    data: tomlkit.TOMLDocument = tomlkit.parse(pyproject.read_text())
    # Update dependency
    _update_dependency(data, package_name, version)
    # Constraints
    _update_constraints(data, constraints)
    # Update pyproject
    pyproject.write_text(tomlkit.dumps(data))
