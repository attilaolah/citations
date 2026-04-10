"""Shared JSON and mapping output helpers for extraction tools."""

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from pathlib import Path


type StrFn = Callable[[str], str]


def write_json_file(path: Path, value: object, *, sort_keys: bool = False) -> None:
    """Write JSON with repository-standard formatting and trailing newline."""
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=sort_keys) + "\n",
        encoding="utf-8",
    )


def sorted_text_set_mapping(
    mapping: Mapping[str, set[str]],
    key_sort: StrFn = str.casefold,
    value_sort: StrFn = str.casefold,
) -> dict[str, list[str]]:
    """Convert ``dict[str, set[str]]`` to deterministically sorted list mapping.

    Returns:
        Mapping with sorted keys and per-key sorted string lists.
    """
    return {
        key: sorted(values, key=value_sort)
        for key, values in sorted(mapping.items(), key=lambda item: key_sort(item[0]))
    }
