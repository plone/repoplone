from .repository import RepositorySettings
from packaging.requirements import Requirement
from typing import NotRequired
from typing import Protocol
from typing import TypedDict


Requirements = dict[str, Requirement]


class PackageConstraintInfo(TypedDict):
    """Definition on a Package constraint information."""

    type: str
    url: str
    warning: NotRequired[str]


class VersionChecker(Protocol):
    """Protocol for version checkers."""

    def __call__(self, settings: RepositorySettings) -> tuple[str, str, str]: ...


class VersionUpgrader(Protocol):
    """Protocol for version upgraders."""

    def __call__(self, settings: RepositorySettings, version: str) -> bool: ...


class MrsDeveloperEntry(TypedDict):
    """Definition of a mrs.developer.json entry."""

    package: str
    url: str
    https: str
    tag: str
    output: NotRequired[str]
    filterBlobs: bool
    develop: bool
