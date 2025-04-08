from dynaconf import Dynaconf


def parse_config() -> Dynaconf:
    """Parse repo settings."""
    settings = Dynaconf(
        settings_files=["repository.toml"],
        merge_enabled=False,
    )
    return settings
