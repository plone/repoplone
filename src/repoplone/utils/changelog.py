from ._path import change_cwd
from click.testing import CliRunner
from datetime import datetime
from pathlib import Path
from repoplone import _types as t
from repoplone import utils
from towncrier._builder import find_fragments
from towncrier._settings import load_config_from_options
from towncrier._shell import cli as towncrier_app


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
    runner = CliRunner()
    args = [
        "build",
        "--config",
        f"{config}",
        "--yes",
        "--name",
        f"'{name}'",
        "--version",
        version,
    ]
    if draft:
        args.append("--draft")
    with change_cwd(cwd):
        result = runner.invoke(towncrier_app, args)
    return result.stdout


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
    for section_id, section_data in sections.items():
        if section_id == "repository":
            has_root = True
        section_name = section_data["name"]
        text = section_data["changes"]
        new_entry = f"{new_entry}\n### {section_name}\n{text}"

    text = f"{changelog_text}".replace(
        CHANGELOG_PLACEHOLDER, f"{CHANGELOG_PLACEHOLDER}\n{new_entry}"
    )
    if not draft:
        root_changelog.write_text(text)
        if has_root:
            # Cleanup top-level news folder
            _cleanup_news(settings.root_path, settings.towncrier.repository.path)

    return new_entry, text


def update_backend_changelog(
    settings: t.RepositorySettings, draft: bool = True, version: str = ""
) -> str:
    config_path = settings.towncrier.backend.path
    result = _run_towncrier(
        config_path, name=settings.name, version=version, draft=draft
    )
    if draft:
        result = _cleanup_draft(result, True)
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
