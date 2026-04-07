"""Pytest that checks unexpected homonyms in Hungarian vernacular names."""

import os
import sys
from collections import defaultdict
from pathlib import Path

import pytest
from pydantic import BaseModel, TypeAdapter


class VernacularName(BaseModel):
    """Vernacular value emitted by the clean pairs pipeline."""

    canonical: str | None = None
    verbatim: str


class CleanEntry(BaseModel):
    """Subset of cleaned entry data required by this test."""

    normalized: str
    vernacular: dict[str, list[VernacularName]] | None = None


CLEAN_ENTRIES_ADAPTER = TypeAdapter(list[CleanEntry])


def _load_known_homonyms(path: Path) -> set[str]:
    known: set[str] = set()
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.split("#", 1)[0].strip()
        if stripped:
            known.add(stripped)
    return known


def _clean_paths() -> list[Path]:
    value = os.environ.get("CLEAN_JSONS")
    if not value:
        return []
    return [Path(item) for item in value.split(":") if item]


def _name_key(name: VernacularName) -> str:
    return name.canonical or name.verbatim


@pytest.fixture(scope="session")
def known_homonyms() -> set[str]:
    """Return known homonyms listed in the external text file."""
    return _load_known_homonyms(Path(os.environ["KNOWN_HOMONYMS"]))


@pytest.fixture(scope="session")
def clean_entries_by_file() -> dict[str, list[CleanEntry]]:
    """Load all clean JSON inputs and return them keyed by file path.

    Returns:
        Parsed clean entries grouped by the input clean JSON path.
    """
    paths = _clean_paths()
    assert paths, "No clean JSON inputs found (CLEAN_JSONS is empty)."
    return {str(path): CLEAN_ENTRIES_ADAPTER.validate_json(path.read_bytes()) for path in sorted(paths, key=str)}


def test_homonyms_are_known(
    known_homonyms: set[str],
    clean_entries_by_file: dict[str, list[CleanEntry]],
) -> None:
    """Fail if a non-whitelisted HU vernacular name maps to multiple scientific names."""
    by_vernacular: dict[str, set[str]] = defaultdict(set)
    for entries in clean_entries_by_file.values():
        for entry in entries:
            vernacular = entry.vernacular
            if not vernacular:
                continue
            for name in vernacular.get("hu", []):
                by_vernacular[_name_key(name)].add(entry.normalized)

    unexpected = {
        vernacular: scientific_names
        for vernacular, scientific_names in by_vernacular.items()
        if len(scientific_names) > 1 and vernacular not in known_homonyms
    }
    details = [
        f"{vernacular} ({len(scientific_names)}): {', '.join(sorted(scientific_names))}"
        for vernacular, scientific_names in sorted(unexpected.items())
    ]
    assert not details, "Unexpected homonyms in Hungarian vernacular names:\n" + "\n".join(details)


if __name__ == "__main__":
    raise SystemExit(pytest.main(sys.argv[1:]))
