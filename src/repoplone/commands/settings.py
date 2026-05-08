from repoplone import _types as t
from repoplone.app import RepoPlone
from repoplone.release.steps import BUILTIN_STEPS
from repoplone.release.steps.local_step import _resolve_entrypoint
from repoplone.utils import display as dutils
from repoplone.utils import settings as utils

import json
import typer


app = RepoPlone()


def _function_id_for(step: t.PipelineReleaseStep) -> str:
    for func_id, builtin in BUILTIN_STEPS.items():
        if builtin.func is step.func:
            return func_id
    return "unknown"


def _source_label(step: t.PipelineReleaseStep, function_id: str) -> str:
    return "built-in" if step.id == function_id else "registered"


@app.command()
def dump(ctx: typer.Context):
    """Dumps the current repository settings as JSON."""
    settings: t.RepositorySettings = ctx.obj.settings
    data = utils.settings_to_dict(settings)
    result = json.dumps(data, indent=2)
    dutils.print_json(result)


@app.command(name="sanity-check")
def sanity_check(ctx: typer.Context):
    """Validate `repository.toml` and resolve every release step.

    Loading the settings already validates `[repository.release]`. This command
    additionally resolves every `local_step` registered alias against the
    project root, so import errors surface here rather than mid-release.
    """
    settings: t.RepositorySettings = ctx.obj.settings
    failures: list[str] = []
    for step in settings.release_steps:
        function_id = _function_id_for(step)
        if function_id != "local_step":
            continue
        entrypoint = step.kwargs.get("entrypoint", "")
        try:
            _resolve_entrypoint(entrypoint, settings.root_path)
        except (
            ValueError,
            ImportError,
            AttributeError,
            TypeError,
        ) as exc:
            failures.append(f"step {step.id!r}: {type(exc).__name__}: {exc}")
    if failures:
        dutils.print("[bold red]Settings sanity check failed:[/bold red]")
        for failure in failures:
            dutils.print(f"  - {failure}")
        raise typer.Exit(code=1)
    dutils.print(
        f"[bold green]Settings OK[/bold green] — {len(settings.release_steps)} "
        "release steps resolved."
    )


@app.command(name="release-steps")
def release_steps(
    ctx: typer.Context,
    output_json: bool = typer.Option(
        False, "--json", help="Emit the pipeline as JSON instead of a table."
    ),
):
    """Show the ordered list of release pipeline steps."""
    settings: t.RepositorySettings = ctx.obj.settings
    rows = []
    for step in settings.release_steps:
        function_id = _function_id_for(step)
        rows.append({
            "id": step.id,
            "title": step.title,
            "function": function_id,
            "source": _source_label(step, function_id),
        })
    if output_json:
        dutils.print_json(json.dumps(rows, indent=2))
        return
    cols = [
        {"header": "Id"},
        {"header": "Title"},
        {"header": "Function"},
        {"header": "Source"},
    ]
    table = dutils.table(
        "Release pipeline steps",
        cols,
        [(r["id"], r["title"], r["function"], r["source"]) for r in rows],
    )
    dutils.print(table)
