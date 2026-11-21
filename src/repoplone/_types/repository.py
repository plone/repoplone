from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from packaging.requirements import Requirement
from pathlib import Path
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from repoplone._types.pipeline import PipelineReleaseStep


Requirements = dict[str, Requirement]

#: Package families. The language prefix of a package type decides how the
#: package is built, versioned and published, so it is what packages group by.
FAMILY_PYTHON = "python"
FAMILY_NODE = "node"

#: Canonical package types, mapped to the family they belong to.
PACKAGE_FAMILIES: dict[str, str] = {
    "python-plone": FAMILY_PYTHON,
    "python": FAMILY_PYTHON,
    "node-volto": FAMILY_NODE,
    "node-aurora": FAMILY_NODE,
    "node": FAMILY_NODE,
}

#: Deprecated spellings accepted when reading a file, so a hand-migrated
#: ``repository.toml`` still loads. ``settings migrate`` writes the canonical
#: name, and the documentation only mentions those.
PACKAGE_TYPE_ALIASES: dict[str, str] = {
    "backend": "python-plone",
    "frontend": "node-volto",
}

#: Base package assumed for a type when the file does not name one. A type
#: absent from this mapping has no default: either it has no ecosystem to
#: build on, or the file must declare one.
DEFAULT_BASE_PACKAGES: dict[str, str] = {
    "python-plone": "Products.CMFPlone",
    "node-volto": "@plone/volto",
    "node-aurora": "@plone/aurora",
}


def resolve_primary(packages: list[Package], family: str) -> Package | None:
    """Return the primary package of a family.

    An explicit ``primary = true`` wins; otherwise the first package of the
    family in document order is primary, which is what a single-package family
    has always meant.

    :param packages: Packages to pick from.
    :param family: Family name, :data:`FAMILY_PYTHON` or :data:`FAMILY_NODE`.
    :returns: The primary package, or ``None`` when the family is empty.
    """
    family_packages = [package for package in packages if package.family == family]
    for package in family_packages:
        if package.primary:
            return package
    return family_packages[0] if family_packages else None


@dataclass
class Changelogs:
    """Changelog locations."""

    root: Path
    backend: Path
    frontend: Path

    def sanity(self) -> bool:
        return self.root.exists()


@dataclass
class Package:
    """Package information."""

    enabled: bool
    name: str
    path: Path
    changelog: Path
    towncrier: Path
    base_package: str
    code_path: Path
    base_package_version: str = ""
    publish: bool = True
    version: str = ""
    type: str = ""
    primary: bool = False
    section: str = ""

    @property
    def family(self) -> str:
        """Return the family this package belongs to, or an empty string."""
        return PACKAGE_FAMILIES.get(self.type, "")

    def sanity(self) -> bool:
        if not self.enabled:
            return True
        return (
            self.path.exists() and self.changelog.exists() and self.towncrier.exists()
        )


@dataclass
class BackendPackage(Package):
    """Backend package information."""

    managed_by_uv: bool = False
    python_version: str = ""
    python_versions: list[str] = field(default_factory=list)
    plone_versions: list[str] = field(default_factory=list)


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
    changelog: Path | None = None

    def sanity(self) -> bool:
        return self.path.exists() if self.path else False


#: Spec 1 names for the two family sections, still accepted as attributes so
#: ``settings.towncrier.backend`` keeps working.
TOWNCRIER_SECTION_ALIASES: dict[str, str] = {
    "backend": FAMILY_PYTHON,
    "frontend": FAMILY_NODE,
}


@dataclass
class TowncrierSettings:
    """Towncrier settings."""

    sections: list[TowncrierSection]

    def get(self, section_id: str) -> TowncrierSection | None:
        """Return a section by id, or ``None``.

        Non-primary packages get ids such as ``python:acme.theme``, which are
        not attribute names, so they are reached through here.

        :param section_id: Id of the section.
        :returns: The section, or ``None`` when no section has that id.
        """
        section_id = TOWNCRIER_SECTION_ALIASES.get(section_id, section_id)
        for section in self.sections:
            if section.section_id == section_id:
                return section
        return None

    def __getattr__(self, name: str):
        section = self.get(name)
        if section is None:
            raise AttributeError(f"{name} not found")
        return section

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
    container_images_prefix: str
    backend: BackendPackage
    frontend: FrontendPackage
    version_path: Path
    compose_path: list[Path]
    towncrier: TowncrierSettings
    changelogs: Changelogs
    release_steps: list[PipelineReleaseStep] = field(default_factory=list)
    remote_origin: str = ""
    issues_url: str = ""
    spec_version: int = 1
    packages: list[Package] = field(default_factory=list)
    _tmp_changelog: str = ""

    @property
    def path(self) -> Path:
        return self.root_path

    def packages_for(self, family: str) -> list[Package]:
        """Return every package of a family, in document order.

        :param family: Family name, :data:`FAMILY_PYTHON` or :data:`FAMILY_NODE`.
        :returns: The packages of that family.
        """
        return [package for package in self.packages if package.family == family]

    def primary(self, family: str) -> Package | None:
        """Return the primary package of a family.

        The primary package owns the component-level settings: the base package
        and its constraints, the lockfiles, ``mrs.developer.json``.

        :param family: Family name, :data:`FAMILY_PYTHON` or :data:`FAMILY_NODE`.
        :returns: The primary package, or ``None`` when the family is empty.
        """
        return resolve_primary(self.packages, family)

    def sanity(self) -> bool:
        steps = [
            self.root_path.exists(),
            self.version_path.exists(),
            all(path.exists() for path in self.compose_path),
            self.towncrier.sanity(),
            self.changelogs.sanity(),
            *[package.sanity() for package in self.packages],
        ]
        if not self.packages:
            # Spec 1 keeps checking the disabled placeholders.
            steps.extend([self.backend.sanity(), self.frontend.sanity()])
        return all(steps)
