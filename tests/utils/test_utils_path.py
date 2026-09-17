from pathlib import Path
from repoplone.utils._path import frontend_root

import pytest


ROOT = Path("/repo")


@pytest.mark.parametrize(
    "package_path,expected",
    [
        # The cookieplone layout: the workspace root is frontend/.
        ["/repo/frontend/packages/volto-addon", "/repo/frontend"],
        ["/repo/frontend/packages/another-addon", "/repo/frontend"],
        # Deeper nesting keeps walking two levels up.
        ["/repo/frontend/packages/scope/addon", "/repo/frontend/packages"],
        # A package directly under frontend/ would walk up to the repository
        # root, and one at the root itself would walk out of the repository.
        # Both fall back to the conventional frontend/ directory.
        ["/repo/frontend/addon", "/repo/frontend"],
        ["/repo/frontend", "/repo/frontend"],
        ["/repo", "/repo/frontend"],
    ],
)
def test_frontend_root(package_path: str, expected: str):
    assert frontend_root(ROOT, Path(package_path)) == Path(expected)


def test_frontend_root_never_escapes_the_repository():
    """Walking two levels up must not leave the repository.

    A frontend package declared as ``path = "frontend"`` sits one level below
    the root, so the naive derivation would point at the repository's parent
    and write files outside it.
    """
    for package_path in (ROOT / "frontend", ROOT):
        result = frontend_root(ROOT, package_path)
        assert result.is_relative_to(ROOT)
