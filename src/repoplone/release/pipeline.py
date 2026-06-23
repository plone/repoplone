from repoplone._types import RepositorySettings
from repoplone.release import _types as t
from repoplone.release.steps.version import resolve_skipped_version
from repoplone.utils import display as dutils


NO_VERSION: str = "next"


def resolve_start(steps: list[t.PipelineReleaseStep], start_step: str) -> int:
    """Return the 0-based index of ``start_step`` within ``steps``.

    :param steps: resolved release steps for the repository.
    :param start_step: id of the step to restart from; empty means start from
        the beginning.
    :returns: index into ``steps`` of the first step to execute.
    :raises ValueError: if ``start_step`` is not a known step id.
    """
    if not start_step:
        return 0
    ids = [step.id for step in steps]
    if start_step not in ids:
        valid = ", ".join(ids)
        raise ValueError(f"Unknown start step {start_step!r}. Valid steps: {valid}.")
    return ids.index(start_step)


class ReleasePipeline:
    """Pipeline to release a project."""

    steps: list[t.PipelineReleaseStep]
    state: t.PipelineState

    def __init__(
        self,
        settings: RepositorySettings,
        dry_run: bool = False,
        desired_version: str = "",
        start_step: str = "",
    ) -> None:
        # Populate steps from settings (parsed from [repository.release])
        self.steps = []
        for step in settings.release_steps:
            if step.id == "release_backend" and not settings.backend.enabled:
                continue
            if step.id == "release_frontend" and not settings.frontend.enabled:
                continue
            self.steps.append(step)

        # Repository settings
        self.settings = settings
        # Version information
        original_version = settings.version
        version_format = settings.version_format
        desired_version = desired_version if desired_version != NO_VERSION else ""
        # Restart support: skip every step before ``start_step``
        self.start_index = resolve_start(self.steps, start_step)
        skipped_ids = {step.id for step in self.steps[: self.start_index]}
        if "version" in skipped_ids:
            # The version step is skipped, so resolve and validate the version
            # supplied on the command line in its place.
            desired_version = resolve_skipped_version(
                settings, original_version, desired_version
            )
        # State
        self.state = t.PipelineState(
            dry_run=dry_run,
            version_format=version_format,
            original_version=original_version,
            next_version=desired_version,
            steps_total=len(self.steps),
        )

    def __call__(self) -> bool:
        """Run the release pipeline."""
        settings = self.settings
        state = self.state
        # Run release steps
        for step_index, step in enumerate(self.steps, start=1):
            state.steps_current = step_index
            if step_index <= self.start_index:
                # Step precedes the requested start step: treat it as already
                # completed in a previous run and skip its execution.
                dutils.print(
                    f"\n[dim]{step_index:02d}/{state.steps_total:02d} "
                    f"{step.title} (skipped)[/dim]"
                )
                continue
            dutils.print(
                f"\n[bold green]{step_index:02d}/{state.steps_total:02d}[/bold green] "
                f"[bold]{step.title}[/bold]"
            )
            if not step.func(step.id, step.title, settings, state, **step.kwargs):
                raise RuntimeError(f"Release step {step.id} failed.")

        return True
