from dynaconf import Dynaconf
from dynaconf.base import LazySettings


def parse_config() -> LazySettings:
    """Parse repo settings."""
    settings = Dynaconf(
        settings_files=["repository.toml"],
        merge_enabled=False,
    )
    return settings
