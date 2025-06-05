from dataclasses import dataclass
from packaging.requirements import Requirement
from pathlib import Path
from typing import TypedDict


Requirements = dict[str, Requirement]


@dataclass
class Changelogs:
    """Changelog locations."""

    root: Path
    backend: Path
    frontend: Path

    def sanity(self) -> bool:
        return self.root.exists() and self.backend.exists() and self.frontend.exists()


@dataclass
class Package:
    """Package information."""

    enabled: bool
    name: str
    path: Path
    changelog: Path
    towncrier: Path
    base_package: str
    base_package_version: str = ""
    publish: bool = True
    version: str = ""

    def sanity(self) -> bool:
        return self.enabled and (
            self.path.exists() and self.changelog.exists() and self.towncrier.exists()
        )


@dataclass
class BackendPackage(Package):
    """Backend package information."""

    managed_by_uv: bool = False


@dataclass
class FrontendPackage(Package):
    """Frontend package information."""

    volto_version: str = ""


@dataclass
class TowncrierSection:
    """Towncrier section."""

    section_id: str
    name: str
    path: Path

    def sanity(self) -> bool:
        return self.path.exists() if self.path else False


@dataclass
class TowncrierSettings:
    """Towncrier settings."""

    sections: list[TowncrierSection]

    def __getattr__(self, name: str):
        for section in self.sections:
            if section.section_id == name:
                return section
        raise AttributeError(f"{name} not found")

    def sanity(self) -> bool:
        sections = self.sections
        checks = [section.sanity() for section in sections]
        return all(checks)


@dataclass
class RepositorySettings:
    """Settings for a distribution."""

    name: str
    managed_by_uv: bool
    root_path: Path
    version: str
    version_format: str
    backend: BackendPackage
    frontend: FrontendPackage
    version_path: Path
    compose_path: list[Path]
    towncrier: TowncrierSettings
    changelogs: Changelogs
    remote_origin: str
    _tmp_changelog: str = ""

    @property
    def path(self) -> Path:
        return self.root_path

    def sanity(self) -> bool:
        steps = [
            self.root_path.exists(),
            self.backend.sanity(),
            self.frontend.sanity(),
            self.version_path.exists(),
            all(path.exists() for path in self.compose_path),
            self.towncrier.sanity(),
            self.changelogs.sanity(),
        ]
        return all(steps)


@dataclass
class CTLContextObject:
    """Context object used by cli."""

    settings: RepositorySettings


class PackageConstraintInfo(TypedDict):
    """Definition on a Package constraint information."""

    type: str
    url: str
