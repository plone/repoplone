from collections.abc import Iterable
from repoplone.utils import toml
from tomlkit.items import Array

import pytest


TROVE_CLASSIFIERS = [
    "Programming Language :: Python :: 3.12",
    "Development Status :: 3 - Alpha",
    "Environment :: Web Environment",
    "Framework :: Plone",
    "Framework :: Plone :: 6.1",
    "Framework :: Plone :: 6.2",
    "Framework :: Plone :: 6.2",
    "Framework :: Plone :: Addon",
    "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.11",
]

DEDUPLICATED_TROVE_CLASSIFIERS = list(set(TROVE_CLASSIFIERS))
SORTED_TROVE_CLASSIFIERS = sorted(TROVE_CLASSIFIERS)


@pytest.mark.parametrize(
    "items,deduplicate,sort_items,first_item,total",
    [
        (TROVE_CLASSIFIERS, False, False, TROVE_CLASSIFIERS[0], len(TROVE_CLASSIFIERS)),
        (
            TROVE_CLASSIFIERS,
            True,
            False,
            DEDUPLICATED_TROVE_CLASSIFIERS[0],
            len(DEDUPLICATED_TROVE_CLASSIFIERS),
        ),
        (
            TROVE_CLASSIFIERS,
            True,
            True,
            SORTED_TROVE_CLASSIFIERS[0],
            len(DEDUPLICATED_TROVE_CLASSIFIERS),
        ),
    ],
)
def test_multiline_array_from_iter(
    items: Iterable[str],
    deduplicate: bool,
    sort_items: bool,
    first_item: str,
    total: int,
):
    """Test repoplone.utils.toml.multiline_array_from_iter"""
    func = toml.multiline_array_from_iter
    results = func(items, deduplicate, sort_items)
    assert isinstance(results, Array)
    assert len(results) == total
    assert results[0] == first_item
