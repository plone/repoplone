from repoplone import _types as t
from repoplone import logger
from repoplone import utils
from repoplone.utils import dependencies
from typing import Annotated

import typer


app = typer.Typer()


@app.command()
def info(ctx: typer.Context):
    """Report the base package in use."""
    settings: t.RepositorySettings = ctx.obj.settings
    if not settings.managed_by_uv:
        typer.echo("Only available for installations managed by uv.")
        raise typer.Exit(1)
    package_name: str = settings.backend.base_package
    logger.info(f"The base package is {package_name}")


@app.command()
def check(ctx: typer.Context):
    """Check latest version of base package and compare it to our current pinning."""
    settings: t.RepositorySettings = ctx.obj.settings
    if not settings.managed_by_uv:
        typer.echo("Only available for installations managed by uv.")
        raise typer.Exit(1)
    package_name: str = settings.backend.base_package
    pyproject = utils.get_pyproject(settings)
    current = (
        dependencies.current_base_package(pyproject, package_name)
        if pyproject
        else None
    )
    if not current:
        logger.info(f"{package_name} is not present in {pyproject}")
    else:
        latest_version = dependencies.latest_package_version(package_name)
        logger.info(f"Current version {current}, latest version {latest_version}")


@app.command()
def upgrade(
    ctx: typer.Context,
    version: Annotated[str, typer.Argument(help="New version the base package")],
):
    """Upgrade a base dependency to a newer version."""
    settings: t.RepositorySettings = ctx.obj.settings
    if not settings.managed_by_uv:
        typer.echo("Only available for installations managed by uv.")
        raise typer.Exit(1)
    package_name: str = settings.backend.base_package
    logger.info(f"Getting {package_name} constraints for version {version}")
    pyproject_path = utils.get_pyproject(settings)
    if pyproject_path and (pyproject := dependencies.parse_pyproject(pyproject_path)):
        existing_pins = dependencies.get_all_pinned_dependencies(pyproject)
        constraints = dependencies.get_package_constraints(
            package_name, version, existing_pins
        )
        logger.info(f"Updating {pyproject_path} dependencies and constraints")
        dependencies.update_pyproject(
            pyproject_path, package_name, version, constraints
        )
        # Update versions.txt
        backend_path = settings.backend.path
        version_file = (backend_path / "version.txt").resolve()
        version_file.write_text(f"{version}\n")
        logger.info("Done")
    else:
        logger.info("No pyproject.toml found")
