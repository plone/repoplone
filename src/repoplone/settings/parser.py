from dynaconf import Dynaconf
from dynaconf.base import LazySettings
from pathlib import Path


SETTINGS_FILE = "repository.toml"


def _default_toml_path() -> Path:
    """Return the default path for the default.toml file."""
    return Path(__file__).parent / "default.toml"


def _find_root_path(settings: LazySettings) -> Path:
    """Return the parent folder of the repository.toml."""
    settings_path = Path(settings.find_file(SETTINGS_FILE))
    parent_path = settings_path.parent.resolve()
    return parent_path


def parse_config(cwd_path: Path) -> LazySettings:
    """Parse repo settings."""
    settings = Dynaconf(
        root_path=cwd_path,
        preload=[_default_toml_path()],
        settings_files=[SETTINGS_FILE],
        merge_enabled=False,
    )
    settings.repository.__root__ = _find_root_path(settings)
    return settings
