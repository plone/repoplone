from packaging.requirements import Requirement
from pathlib import Path
from repoplone import _types as t
from repoplone.utils._requests import get_remote_data
from repoplone.utils.toml import multiline_array_from_iter
from tomlkit import container
from tomlkit import items

import re
import tomlkit


PLONE_VERSION_PATTERN = re.compile(r"^Framework :: Plone :: (\d+\.\d+)$")
PYTHON_VERSION_PATTERN = re.compile(r"^Programming Language :: Python :: (\d+\.\d+)$")
LICENSE_PATTERN = re.compile(r"^License :: (.+)$")


def _get_table(
    data: tomlkit.TOMLDocument | items.Table, key: str
) -> items.Table | container.OutOfOrderTableProxy:
    """Return a table from the given data."""
    table = data[key]
    if not isinstance(table, items.Table | container.OutOfOrderTableProxy):
        raise ValueError("Invalid data")
    return table


def _get_project_table(
    data: tomlkit.TOMLDocument,
) -> items.Table | container.OutOfOrderTableProxy:
    """Return the project table from the given data."""
    return _get_table(data, "project")


def _process_requirements(data: tomlkit.TOMLDocument, key: str) -> list[Requirement]:
    """Return requirements found under a dotted ``pyproject.toml`` key.

    Handles both array tables (e.g. ``project.dependencies``) and grouped
    tables (e.g. ``dependency-groups``).

    :param data: Parsed ``pyproject.toml`` document.
    :param key: Dotted path to the dependency table or array.
    :returns: List of parsed requirements.
    """
    requirements: list[Requirement] = []
    base_table = data
    try:
        for part in key.split(".")[:-1]:
            base_table = base_table.get(part, {})
        raw_dependencies: items.Table | items.Array = (
            base_table.get(key.split(".")[-1])
        ) or tomlkit.table()
    except (KeyError, ValueError):
        raw_dependencies = tomlkit.array()
    if isinstance(raw_dependencies, items.Array):
        tmp_table = tomlkit.table()
        tmp_table.add(key, raw_dependencies)
        raw_dependencies = tmp_table
    if raw_dependencies:
        for group_values in raw_dependencies.values():
            for value in group_values:
                requirements.append(Requirement(value))
    return requirements


def _get_uv_table(data: tomlkit.TOMLDocument) -> items.Table:
    """Return the uv information in pyproject.toml."""
    tool: items.Table | None = data.get("tool")
    uv_config: items.Table | None = tool.get("uv") if tool else None
    if not uv_config:
        uv_config = tomlkit.table()
    return uv_config


def _get_uv_sources_table(data: tomlkit.TOMLDocument) -> items.Table:
    """Return the ``[tool.uv.sources]`` table, or a fresh detached one.

    A returned detached table is not attached to ``data``; callers that mutate
    it must reattach it (see :func:`_ensure_uv_table`).

    :param data: Parsed ``pyproject.toml`` document.
    :returns: The existing sources table or a new empty table.
    """
    uv_config = _get_uv_table(data)
    sources_table: items.Table | None = uv_config.get("sources") if uv_config else None
    return sources_table if sources_table else tomlkit.table()


def _ensure_uv_table(data: tomlkit.TOMLDocument) -> items.Table:
    """Return the ``[tool.uv]`` table, creating and attaching it when absent.

    :param data: Parsed ``pyproject.toml`` document to mutate.
    :returns: The ``[tool.uv]`` table attached to ``data``.
    """
    tool = data.get("tool")
    if tool is None:
        tool = tomlkit.table(True)
        data["tool"] = tool
    uv_config = tool.get("uv")
    if uv_config is None:
        uv_config = tomlkit.table()
        tool["uv"] = uv_config
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
        "tool.uv.override-dependencies",
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


def _uv_add_source_package(
    data: tomlkit.TOMLDocument, package: str, version: str
) -> None:
    """Pin a base package to a Git branch via ``[tool.uv.sources]``.

    :param data: Parsed ``pyproject.toml`` document to mutate.
    :param package: Name of the base package.
    :param version: Branch reference in ``@branch`` form.
    :raises RuntimeError: If the package has no repository information.
    """
    from repoplone.utils.dependencies.constraints import get_constraint_info

    pkg_config = get_constraint_info(package)
    if not (repository_info := pkg_config.get("repository")):
        raise RuntimeError(
            f"Package {package} does not have repository information, "
            "cannot use branch installation."
        )
    branch = version[1:]
    sources_table = _get_uv_sources_table(data)
    package_info = tomlkit.inline_table()
    # Pad the inline table so it renders as ``{ git = "...", branch = "..." }``.
    package_info.add(tomlkit.ws(" "))
    package_info.add("git", repository_info["url"])
    package_info.add("branch", branch)
    if subdir := repository_info.get("subdirectory"):
        package_info.add("subdirectory", subdir)
    package_info.add(tomlkit.ws(" "))
    sources_table.add(package, package_info)
    # Reattach the sources table in case it was created detached.
    _ensure_uv_table(data)["sources"] = sources_table


def _uv_remove_source_package(data: tomlkit.TOMLDocument, package: str) -> None:
    """Remove a source package from the ``[tool.uv.sources]`` table.

    :param data: Parsed ``pyproject.toml`` document to mutate.
    :param package: Name of the package to remove.
    """
    sources_table = _get_uv_sources_table(data)
    sources_table.pop(package, None)


def _update_dependency(data: tomlkit.TOMLDocument, package: str, version: str) -> None:
    """Update the base package pin in ``project.dependencies``.

    For a regular version the dependency is pinned with ``==``. For a branch
    (``@branch``) the version pin is dropped and the package is wired to a Git
    source via ``[tool.uv.sources]``.

    :param data: Parsed ``pyproject.toml`` document to mutate.
    :param package: Name of the base package.
    :param version: Version to pin, or ``@branch`` to install from a branch.
    """
    if from_branch := version.startswith("@"):
        _uv_add_source_package(data, package, version)
    else:
        # Removing a non-existent source is a no-op, so this is always safe.
        _uv_remove_source_package(data, package)
    project = _get_project_table(data)
    deps = tomlkit.array()
    deps.multiline(True)
    project_dependencies = _get_project_dependencies(data)
    for dep_name in project_dependencies:
        if dep_name == package:
            dep = package if from_branch else f"{package}=={version}"
        else:
            # Keep dependency as stated before
            dep = str(project_dependencies[dep_name])
        deps.append(dep)
    project.update({"dependencies": deps})


def _update_constraints(data: tomlkit.TOMLDocument, raw_constraints: list[str]) -> None:
    """Write resolved constraints into ``[tool.uv] constraint-dependencies``.

    :param data: Parsed ``pyproject.toml`` document to mutate.
    :param raw_constraints: Constraint specifiers to write (sorted on output).
    """
    tool_uv = _ensure_uv_table(data)
    # We should sort items here to maintain consistency
    constraints = multiline_array_from_iter(raw_constraints, True, True)
    tool_uv.update({"constraint-dependencies": constraints})


def _add_versions_to_classifiers(
    classifiers: set[str], prefix: str, versions: list[str]
) -> None:
    """Add ``<prefix> <version>`` trove classifiers to a classifier set.

    :param classifiers: Set of classifiers to update in place.
    :param prefix: Classifier prefix (e.g. ``Framework :: Plone ::``).
    :param versions: Versions to append to the prefix.
    """
    prefix = prefix[:-1] if prefix.endswith(" ") else prefix
    for version in versions:
        classifiers.add(f"{prefix} {version}")


def _handle_license_classifier(
    project: items.Table | container.OutOfOrderTableProxy, classifiers: set[str]
) -> None:
    """Remove classifier for license IF license is present on the project table."""
    license_ = project.get("license", None)
    if not license_:
        return
    for classifier in list(classifiers):
        if LICENSE_PATTERN.match(classifier):
            classifiers.remove(classifier)


def _update_classifiers(
    data: tomlkit.TOMLDocument, python_versions: list[str], plone_versions: list[str]
) -> None:
    """Refresh the Python, Plone and license trove classifiers in place.

    Existing Python and Plone version classifiers are removed and replaced with
    the supplied versions; the license classifier is dropped when the project
    declares an explicit ``license``.

    :param data: Parsed ``pyproject.toml`` document to mutate.
    :param python_versions: Supported Python versions.
    :param plone_versions: Supported Plone versions.
    """
    project = _get_project_table(data)
    classifiers: set[str] = set(project.get("classifiers", []))
    # First handle license classifier
    _handle_license_classifier(project, classifiers)
    # Remove existing Python and Plone version classifiers
    for classifier in list(classifiers):
        if PYTHON_VERSION_PATTERN.match(classifier) or PLONE_VERSION_PATTERN.match(
            classifier
        ):
            classifiers.remove(classifier)
    # Add updated Python version classifiers
    _add_versions_to_classifiers(
        classifiers, "Programming Language :: Python ::", python_versions
    )
    # Add updated Plone version classifiers
    _add_versions_to_classifiers(classifiers, "Framework :: Plone ::", plone_versions)

    # Sorting and deduplicating
    new_classifiers = multiline_array_from_iter(classifiers, True, True)
    # Update project classifiers
    project.update({"classifiers": new_classifiers})


def _parse_pyproject(src: str) -> tomlkit.TOMLDocument:
    """Parse ``pyproject.toml`` content into a TOML document.

    :param src: Raw ``pyproject.toml`` text.
    :returns: Parsed TOML document.
    """
    return tomlkit.parse(src)


def parse_pyproject(pyproject: Path) -> tomlkit.TOMLDocument:
    """Parse a ``pyproject.toml`` file into a TOML document.

    :param pyproject: Path to the ``pyproject.toml`` file.
    :returns: Parsed TOML document.
    """
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


def license_from_project(data: tomlkit.TOMLDocument) -> str:
    """Return the license listed on the project."""
    project = _get_project_table(data)
    license_ = project.get("license")
    return str(license_) if license_ else ""


def license_from_classifier(data: tomlkit.TOMLDocument) -> list[str]:
    """Return the license listed on the classifier."""
    versions = _parse_classifiers(data, LICENSE_PATTERN)
    return versions


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
