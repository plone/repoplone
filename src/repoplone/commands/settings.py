from dataclasses import asdict
from dataclasses import is_dataclass
from pathlib import Path
from pathlib import PosixPath
from repoplone import _types as t
from repoplone.app import RepoPlone
from repoplone.utils import display as dutils
from typing import Any

import json
import typer


app = RepoPlone()


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


def _settings_to_dict(settings: t.RepositorySettings) -> dict[str, Any]:
    """Recursevely convert the settings object to a dictionary."""
    data = asdict(settings)
    return _serialize_dict(data)


@app.command()
def dump(ctx: typer.Context):
    """Dumps the current repository settings as JSON."""
    settings: t.RepositorySettings = ctx.obj.settings
    data = _settings_to_dict(settings)
    result = json.dumps(data, indent=2)
    dutils.print_json(result)
