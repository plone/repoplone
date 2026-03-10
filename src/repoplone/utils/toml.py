from collections.abc import Iterable

import tomlkit


def multiline_array_from_iter(
    raw_items: Iterable[str],
    deduplicate: bool = True,
    sort_items: bool = False,
):
    """Create a TOML multiline array from a list, set, or tuple of strings.

    :param raw_items: The items to include in the array.
    :param deduplicate: If ``True``, items are deduplicated.
    :param sort_items: If ``True``, items are sorted alphabetically before insertion.
    :returns: A tomlkit array configured for multiline formatting.
    """
    items = list(set(raw_items) if deduplicate else raw_items)
    if sort_items:
        items.sort()
    array = tomlkit.array()
    array.multiline(True)
    for line in items:
        item = tomlkit.item(line)
        array.append(item)
    return array
