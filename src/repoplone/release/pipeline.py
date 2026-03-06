from repoplone._types import RepositorySettings
from repoplone.release import _types as t
from repoplone.release.steps import get_steps
from repoplone.utils import display as dutils


NO_VERSION: str = "next"


class ReleasePipeline:
    """Pipeline to release a project."""

    steps: list[t.PipelineReleaseStep]
    state: t.PipelineState

    def __init__(
        self,
        settings: RepositorySettings,
        dry_run: bool = False,
        desired_version: str = "",
    ) -> None:
        # Populate steps
        self.steps = get_steps()
        # Repository settings
        self.settings = settings
        # Version information
        original_version = settings.version
        version_format = settings.version_format
        desired_version = desired_version if desired_version != NO_VERSION else ""
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
            dutils.print(
                f"\n[bold green]{step_index:02d}/{state.steps_total:02d}[/bold green] "
                f"[bold]{step.title}[/bold]"
            )
            if not step.func(step.id, step.title, settings, state):
                raise RuntimeError(f"Release step {step.id} failed.")

        return True
