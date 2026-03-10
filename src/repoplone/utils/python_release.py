from pathlib import Path


DIST_FOLDER_NAME = "dist"
PACKAGE_EXTENSIONS = (".whl", ".tar.gz")


def _dist_folder(cwd: Path | None = None) -> Path | None:
    """Return the path to the folder where we store the release files."""
    cwd = cwd if cwd is not None else Path().cwd()
    path: Path | None = cwd / DIST_FOLDER_NAME
    if not (path and path.exists()):
        path = None
    return path


def list_release_files(cwd: Path | None = None, version: str = "") -> list[Path]:
    """List all release files already built in the current working directory."""
    files: list[Path] = []
    path = _dist_folder(cwd)
    if path:
        glob = f"*{version}*" if version else "*"
        all_files: list[Path] = list(path.glob(glob))
        for file in all_files:
            if not (file.name.endswith(".whl") or file.name.endswith(".tar.gz")):
                continue
            files.append(file)
    return files


def remove_release_files(cwd: Path | None = None, files: list[Path] | None = None):
    """Remove existing release files."""
    files_: list[Path] = files if files is not None else list_release_files(cwd)
    for file in files_:
        if not file.is_file():
            continue
        file.unlink()
