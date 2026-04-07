"""Pytest completeness check for name-pairs extraction."""

import os
import sys
from pathlib import Path

import pytest
from pydantic import BaseModel, TypeAdapter


class CleanName(BaseModel):
    """Subset of cleaned entries required for completeness checks."""

    normalized: str


class GlobalName(BaseModel):
    """Subset of gnfinder output required for completeness checks."""

    name: str


CLEAN_ADAPTER = TypeAdapter(list[CleanName])
GLOBAL_NAMES_ADAPTER = TypeAdapter(list[GlobalName])


@pytest.fixture(scope="session")
def clean_entries() -> list[CleanName]:
    """Provide cleaned entries from environment-provided JSON path.

    Returns:
        Parsed cleaned entries.
    """
    clean_path = Path(os.environ["NAME_PAIRS_COMPLETENESS_CLEAN_PATH"])
    return CLEAN_ADAPTER.validate_json(clean_path.read_bytes())


@pytest.fixture(scope="session")
def global_name_entries() -> list[GlobalName]:
    """Provide gnfinder entries from environment-provided JSON path.

    Returns:
        Parsed gnfinder entries.
    """
    global_names_path = Path(os.environ["NAME_PAIRS_COMPLETENESS_GLOBAL_NAMES_PATH"])
    return GLOBAL_NAMES_ADAPTER.validate_json(global_names_path.read_bytes())


@pytest.fixture(scope="session")
def ignored_names() -> set[str]:
    """Load ignore-list entries, stripping comments and empty lines.

    Returns:
        Case-sensitive set of ignored names.
    """
    value = os.environ["NAME_PAIRS_COMPLETENESS_IGNORE_PATH"]
    if not value:
        return set()

    ignored: set[str] = set()
    for raw_line in Path(value).read_text(encoding="utf-8").splitlines():
        stripped = raw_line.split("#", 1)[0].strip()
        if stripped:
            ignored.add(stripped)
    return ignored


def test_names_are_covered(
    clean_entries: list[CleanName],
    global_name_entries: list[GlobalName],
    ignored_names: set[str],
) -> None:
    """Ensure every gnfinder name is represented in cleaned normalized names."""
    normalized = {entry.normalized.casefold() for entry in clean_entries}
    missing = sorted(
        {
            entry.name
            for entry in global_name_entries
            if entry.name.casefold() not in normalized and entry.name not in ignored_names
        },
    )
    assert not missing, "Names found by gnfinder but missing from cleaned output:\n" + "\n".join(missing)


if __name__ == "__main__":
    raise SystemExit(pytest.main(sys.argv[1:]))
