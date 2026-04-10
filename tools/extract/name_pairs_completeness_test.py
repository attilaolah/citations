"""Pytest completeness check for name-pairs extraction."""

import os
import sys
import unicodedata
from pathlib import Path

import pytest
from pydantic import BaseModel, TypeAdapter

from tools.extract.models import CLEAN_ENTRIES_ADAPTER, CleanEntry


class ScientificName(BaseModel):
    """Subset of gnfinder output required for completeness checks."""

    name: str


SCIENTIFIC_NAMES_ADAPTER = TypeAdapter(list[ScientificName])


@pytest.fixture(scope="session")
def clean_entries() -> list[CleanEntry]:
    """Provide cleaned entries from environment-provided JSON path.

    Returns:
        Parsed cleaned entries.
    """
    clean_path = Path(os.environ["CLEAN"])
    return CLEAN_ENTRIES_ADAPTER.validate_json(clean_path.read_bytes())


@pytest.fixture(scope="session")
def scientific_name_entries() -> list[ScientificName]:
    """Provide gnfinder entries from environment-provided JSON path.

    Returns:
        Parsed gnfinder entries.
    """
    scientific_names_path = Path(os.environ["SCIENTIFIC_NAMES"])
    return SCIENTIFIC_NAMES_ADAPTER.validate_json(scientific_names_path.read_bytes())


@pytest.fixture(scope="session")
def ignored_names() -> set[str]:
    """Load ignore-list entries, stripping comments and empty lines.

    Returns:
        Case-sensitive set of ignored names.
    """
    value = os.environ.get("IGNORE_NAMES")
    if not value:
        return set()

    ignored: set[str] = set()
    for raw_line in Path(value).read_text(encoding="utf-8").splitlines():
        stripped = raw_line.split("#", 1)[0].strip()
        if stripped:
            ignored.add(stripped)
    return ignored


def _is_word_prefix(candidate: str, names: list[str]) -> bool:
    candidate_tokens = _fold(candidate).split()
    if not candidate_tokens:
        return False
    candidate_token_count = len(candidate_tokens)
    for name in names:
        name_tokens = _fold(name).split()
        if len(name_tokens) <= candidate_token_count:
            continue
        if name_tokens[:candidate_token_count] == candidate_tokens:
            return True
    return False


def _exemption_reason(
    name: str,
    normalized_names: set[str],
    normalized_name_list: list[str],
    vernacular_names: set[str],
    vernacular_name_list: list[str],
) -> str | None:
    folded = _fold(name)
    if folded in normalized_names:
        return "present as normalized"
    if _is_word_prefix(name, normalized_name_list):
        return "word prefix of normalized name"
    if folded in vernacular_names:
        return "present as vernacular"
    if _is_word_prefix(name, vernacular_name_list):
        return "word prefix of vernacular name"
    return None


def _fold(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def test_names_are_covered(
    clean_entries: list[CleanEntry],
    scientific_name_entries: list[ScientificName],
    ignored_names: set[str],
) -> None:
    """Ensure every gnfinder name is represented in cleaned normalized names."""
    normalized_name_list = [entry.normalized for entry in clean_entries]
    normalized = {_fold(value) for value in normalized_name_list}

    vernacular_name_list: list[str] = []
    for entry in clean_entries:
        if entry.vernacular is None:
            continue
        for values in entry.vernacular.values():
            for value in values:
                verbatim = value.verbatim
                if verbatim:
                    vernacular_name_list.append(verbatim)
    vernacular = {_fold(value) for value in vernacular_name_list}

    scientific_names = sorted({entry.name for entry in scientific_name_entries})
    missing = sorted(
        {
            name
            for name in scientific_names
            if (
                _exemption_reason(
                    name,
                    normalized,
                    normalized_name_list,
                    vernacular,
                    vernacular_name_list,
                )
                is None
                and name not in ignored_names
            )
        },
    )
    assert not missing, "Names found by gnfinder but missing from cleaned output:\n" + "\n".join(missing)

    scientific_names_folded = {_fold(name) for name in scientific_names}
    unnecessary_ignores = sorted(
        {
            ignored
            for ignored in ignored_names
            if (
                _fold(ignored) not in scientific_names_folded
                or _exemption_reason(
                    ignored,
                    normalized,
                    normalized_name_list,
                    vernacular,
                    vernacular_name_list,
                )
                is not None
            )
        },
    )
    assert (
        not unnecessary_ignores
    ), "Ignore entries are unnecessary (not found in gnfinder output, or already covered):\n" + "\n".join(
        unnecessary_ignores,
    )


if __name__ == "__main__":
    raise SystemExit(pytest.main(sys.argv[1:]))
