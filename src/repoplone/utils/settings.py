from dataclasses import asdict
from dataclasses import is_dataclass
from pathlib import Path
from pathlib import PosixPath
from repoplone import _types as t
from typing import Any


def _serialize_value(value: Any) -> Any:
    if is_dataclass(value):
        value = _serialize_dict(asdict(value))  # type: ignore[arg-type]
    elif isinstance(value, dict):
        value = _serialize_dict(value)
    elif isinstance(value, tuple | set):
        value = list[value]
    elif isinstance(value, list):
        value = [_serialize_value(v) for v in value]
    elif isinstance(value, Path | PosixPath):
        value = str(value)
    return value


def _serialize_dict(data: dict) -> dict:
    for key, value in data.items():
        data[key] = _serialize_value(value)
    return data


def settings_to_dict(settings: t.RepositorySettings) -> dict[str, Any]:
    """Recursevely convert the settings object to a dictionary."""
    data = asdict(settings)
    return _serialize_dict(data)
