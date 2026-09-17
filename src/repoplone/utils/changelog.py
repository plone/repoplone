from datetime import datetime
from pathlib import Path
from repoplone import _types as t
from repoplone import utils
from repoplone.integrations.towncrier import Towncrier
from towncrier._builder import find_fragments
from towncrier._settings import load_config_from_options


CHANGELOG_PLACEHOLDER = "<!-- towncrier release notes start -->"


def _cleanup_draft(text: str, include_version: bool = False) -> str:
    lines = text.split("\n")
    for idx, line in enumerate(lines):
        if line.startswith("## "):
            idx += 0 if include_version else 1
            break
    text = "\n".join(lines[idx:])
    return text


def _prepare_section_changelog(text: str) -> str:
    """Prepare section changelog to be added to the project changelog."""
    text = _cleanup_draft(text)
    # Increase header levels
    text = text.replace("###", "####")
    if not text.strip():
        text = "\nNo significant changes.\n\n"
    return text


def _run_towncrier(config: Path, name: str, version: str, draft: bool = True) -> str:
    cwd = config.parent
    runner = Towncrier(cwd)
    result = runner.run(config=config, name=name, version=version, draft=draft)
    return result


def generate_section_changelogs(
    settings: t.RepositorySettings, version: str = ""
) -> dict[str, dict]:
    sections = {}
    config: t.TowncrierSettings = settings.towncrier
    for section in config.sections:
        config_path = section.path
        result = _run_towncrier(
            config_path, name=settings.name, version=version, draft=True
        )
        sections[section.section_id] = {
            "name": section.name,
            "changes": _prepare_section_changelog(result),
        }
    return sections


def _find_fragments(path: Path, towncrier_settings: Path) -> list[tuple[str, str]]:
    base_directory, config = load_config_from_options(path, towncrier_settings)
    _, fragments = find_fragments(base_directory, config, False)
    return fragments


def _cleanup_news(path: Path, towncrier_settings: Path):
    all_fragments = _find_fragments(path, towncrier_settings)
    for raw_fragment_path, _ in all_fragments:
        fragment_path = Path(raw_fragment_path).resolve()
        # Remove
        fragment_path.unlink()


def _sections_owning_root(settings: t.RepositorySettings) -> set[str]:
    """Return the ids of sections whose package owns the repository changelog.

    A package declared at the repository root points its ``changelog`` at the
    repository changelog, so its own towncrier build writes that file. The
    aggregated entry must then leave it alone.

    :param settings: Repository settings.
    :returns: Section ids to skip when writing the repository changelog.
    """
    root = settings.changelogs.root
    return {
        section.section_id
        for section in settings.towncrier.sections
        if section.section_id != "repository" and section.changelog == root
    }


# Update Changelog at root
def _update_project_changelog(
    settings: t.RepositorySettings,
    sections: dict[str, dict],
    draft: bool = True,
    version: str = "",
) -> tuple[str, str]:
    root_changelog = settings.changelogs.root
    changelog_text = root_changelog.read_text()
    header = f"## {version} ({datetime.now():%Y-%m-%d})"
    new_entry = f"{header}\n"
    has_root = False
    owns_root = _sections_owning_root(settings)
    written_sections = 0
    for section_id, section_data in sections.items():
        if section_id == "repository":
            has_root = True
        if not draft and section_id in owns_root:
            # This package's changelog *is* the repository changelog, and its
            # own towncrier build writes it. Adding a section here too would
            # report every change twice, under two different headings.
            continue
        written_sections += 1
        section_name = section_data["name"]
        text = section_data["changes"]
        new_entry = f"{new_entry}\n### {section_name}\n{text}"

    text = f"{changelog_text}".replace(
        CHANGELOG_PLACEHOLDER, f"{CHANGELOG_PLACEHOLDER}\n{new_entry}"
    )
    if not draft and written_sections:
        root_changelog.write_text(text)
        if has_root:
            # Cleanup top-level news folder
            _cleanup_news(settings.root_path, settings.towncrier.repository.path)

    return new_entry, text


def update_backend_changelog(
    settings: t.RepositorySettings,
    package: t.Package,
    draft: bool = True,
    version: str = "",
) -> str:
    """Build the changelog of one backend package.

    :param settings: Repository settings.
    :param package: Backend package to build the changelog for.
    :param draft: Whether to render a draft instead of writing the changelog.
    :param version: Version to render the changelog for.
    :returns: The rendered changelog, or an empty string for a disabled package.
    """
    if not package.enabled:
        return ""
    result = _run_towncrier(
        package.towncrier, name=package.name, version=version, draft=draft
    )
    if draft:
        result = _cleanup_draft(result, True)
    return result


def update_frontend_changelog(
    settings: t.RepositorySettings,
    package: t.Package,
    draft: bool = True,
    version: str = "",
) -> str:
    """Build the changelog of one frontend package.

    Outside of a draft, the package changelog is also copied over the
    frontend-wide one.

    :param settings: Repository settings.
    :param package: Frontend package to build the changelog for.
    :param draft: Whether to render a draft instead of writing the changelog.
    :param version: Version to render the changelog for.
    :returns: The rendered changelog, or an empty string for a disabled package.
    """
    if not package.enabled:
        return ""
    result = _run_towncrier(
        package.towncrier, name=package.name, version=version, draft=draft
    )
    if draft:
        result = _cleanup_draft(result, True)
    elif package.primary:
        # Copy result to the frontend-wide changelog. Only the primary package
        # does this: with several node packages the last one would win, and the
        # file would report whichever ran last rather than the component.
        package_path = package.path
        package_changelog = Path(package_path) / "CHANGELOG.md"
        frontend_path = utils.frontend_root(settings.root_path, package_path)
        frontend_changelog = Path(frontend_path) / "CHANGELOG.md"
        if frontend_changelog.exists():
            frontend_changelog.write_text(package_changelog.read_text())
    return result


def update_changelog(
    settings: t.RepositorySettings, draft: bool = True, version: str = ""
) -> tuple[str, str]:
    if draft and not version:
        version = utils.get_next_version(settings)
    sections = generate_section_changelogs(settings=settings, version=version)
    return _update_project_changelog(
        settings=settings, sections=sections, version=version, draft=draft
    )
