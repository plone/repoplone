from pathlib import Path
from repoplone import _types as t
from repoplone import logger
from repoplone import utils
from repoplone.app import RepoPlone
from repoplone.integrations.make import Make
from repoplone.utils import dependencies
from repoplone.utils import display as dutils
from typing import Annotated

import typer


app = RepoPlone()


@app.command()
def info(ctx: typer.Context):
    """Report the base packages in use."""
    settings: t.RepositorySettings = ctx.obj.settings
    title = "Base packages"
    cols = [
        {"header": "Component"},
        {"header": "Package Name"},
    ]
    rows = [
        ["Backend", settings.backend.base_package],
        ["Frontend", settings.frontend.base_package],
    ]
    table = dutils.table(title, cols, rows)
    dutils.print(table)


@app.command()
def check(ctx: typer.Context):
    """Check latest version of base package and compare it to our current pinning."""
    settings: t.RepositorySettings = ctx.obj.settings
    backend_versions = dependencies.check_backend_base_package(settings)
    frontend_versions = dependencies.check_frontend_base_package(settings)
    title = "Base packages versions"
    cols = [
        {"header": "Component"},
        {"header": "Package Name"},
        {"header": "Current Version"},
        {"header": "Latest Version"},
    ]
    rows = [
        ["Backend", *backend_versions],
        ["Frontend", *frontend_versions],
    ]
    table = dutils.table(title, cols, rows)
    dutils.print(table)


def _update_constraints(pyproject_path: Path, package_name: str, version: str) -> bool:
    """Update constraints in pyproject.toml."""
    if pyproject := dependencies.parse_pyproject(pyproject_path):
        existing_pins = dependencies.get_all_pinned_dependencies(pyproject)
        constraints = dependencies.get_package_constraints(
            package_name, version, existing_pins
        )
        logger.info(f"Updating {pyproject_path} dependencies and constraints")
        dependencies.update_pyproject(
            pyproject_path, package_name, version, constraints
        )
        return True
    return False


def _upgrade_backend(settings: t.RepositorySettings, version: str) -> bool:
    """Upgrade a base dependency to a newer version."""
    package_name: str = settings.backend.base_package
    logger.info(f"Getting {package_name} constraints for version {version}")
    pyproject_path = utils.get_pyproject(settings)
    if pyproject_path:
        status = _update_constraints(pyproject_path, package_name, version)
        # Update versions.txt if it exists
        backend_path = settings.backend.path
        version_file = (backend_path / "version.txt").resolve()
        if status and version_file.exists():
            version_file.write_text(f"{version}\n")
        return status
    else:
        return False


def _upgrade_frontend(settings: t.RepositorySettings, version: str) -> bool:
    """Upgrade a base dependency to a newer version."""
    package_name: str = settings.frontend.base_package
    return dependencies.update_frontend_base_package(settings, package_name, version)


def _sync_dependencies(
    settings: t.RepositorySettings, component: str, check_constraints: bool = True
):
    """Sync the lockfile for a specific component."""
    towncrier_path = settings.root_path / "news"
    if component == "backend":
        if check_constraints:
            # We need to update the constrains
            info = dependencies.check_backend_base_package(settings)
            package_name, version = info[0:2]
            status = _update_constraints(
                settings.backend.path / "pyproject.toml", package_name, version
            )
        else:
            status = True
        towncrier_path = settings.backend.path / "news"
    else:
        towncrier_path = settings.frontend.path / "news"
        status = True
    if status:
        make = Make(settings.root_path)
        try:
            target = f"{component}-install"
            typer.echo(f" - Will update lockfile by running 'make {target}'")
            make.run(target)
        except RuntimeError as e:
            typer.echo(f" - Error running 'make {target}: {e}")
            raise typer.Exit(1) from e
        typer.echo("\n")
        typer.echo(f"Now, please, add a news entry in {towncrier_path}.")


@app.command()
def sync(
    ctx: typer.Context,
    component: Annotated[
        str,
        typer.Argument(
            help="Which component to sync the lockfile? backend or frontend"
        ),
    ] = "both",
):
    """Sync the lockfile for a specific component."""
    settings: t.RepositorySettings = ctx.obj.settings
    if component not in ("backend", "frontend", "both"):
        typer.echo("Component must be either 'backend' or 'frontend'.")
        raise typer.Exit(1)
    components = [component] if component != "both" else ["backend", "frontend"]
    for component_ in components:
        _sync_dependencies(settings, component_)
        typer.echo("\n")


UPGRADE_FUNC: dict[str, tuple[t.VersionChecker, t.VersionUpgrader]] = {
    "backend": (dependencies.check_backend_base_package, _upgrade_backend),
    "frontend": (dependencies.check_frontend_base_package, _upgrade_frontend),
}


@app.command()
def upgrade(
    ctx: typer.Context,
    component: Annotated[
        str, typer.Argument(help="Which component to upgrade? backend or frontend?")
    ],
    version: Annotated[
        str, typer.Argument(help="New version the base package")
    ] = "latest",
):
    """Upgrade a base dependency to a newer version."""
    settings: t.RepositorySettings = ctx.obj.settings
    if component not in ("backend", "frontend"):
        typer.echo("Component must be either 'backend' or 'frontend'.")
        raise typer.Exit(1)
    info_func, upgrade_func = UPGRADE_FUNC[component]

    try:
        info = info_func(settings)
    except RuntimeError as e:
        typer.echo(f" - Error checking {component} base package: {e}")
        raise typer.Exit(1) from e
    package_name, current_version = info[0:2]
    if version == "latest":
        version = info[2]  # Latest version
    package_title = f"{package_name} ({component.title()})"
    if version != current_version:
        typer.echo(f"Upgrade {package_title} from {current_version} to {version}")
        if upgrade_func(settings, version):
            typer.echo(f"- {package_title} at version {version}.")
            _sync_dependencies(settings, component, check_constraints=False)
        else:
            typer.echo(f"- Failed to upgrade {package_title} to version {version}.")
            raise typer.Exit(1)
    else:
        typer.echo(f"{package_title} already at version {version}.")
