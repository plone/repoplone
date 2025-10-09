from datetime import date


CALVER_BUMPS = [
    "calver",
]


def bumps() -> list[str]:
    """Return the list of supported version bumps."""
    return CALVER_BUMPS


def next_version(desired_version: str, original_version: str) -> str:
    """Return the next calver version for this project.

    desired_version could be "calver" to get today's date
    """
    if desired_version not in CALVER_BUMPS:
        raise ValueError(f"Unsupported calver bump: {desired_version}")

    base_version, minor = original_version.split(".")
    today = date.today().strftime("%Y%m%d")
    if today == base_version:
        next_minor = int(minor) + 1
        nv = f"{today}.{next_minor}"
    else:
        nv = f"{today}.1"
    return nv
