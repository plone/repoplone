from dataclasses import dataclass
from repoplone._types.repository import RepositorySettings
from typing import Protocol


@dataclass
class PipelineState:
    """A run of the pipeline."""

    dry_run: bool = False
    version_format: str = "semver"
    original_version: str = ""
    next_version: str = ""
    steps_current: int = 0
    steps_total: int = 0


class PipelineReleaseStepFunction(Protocol):
    def __call__(
        self,
        step_id: str,
        title: str,
        settings: RepositorySettings,
        run: PipelineState,
    ) -> bool: ...


@dataclass
class PipelineReleaseStep:
    """Definition of a release step."""

    id: str
    title: str
    func: PipelineReleaseStepFunction
