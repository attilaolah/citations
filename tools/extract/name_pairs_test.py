"""Pytest tests for name-pairs validation."""

import os
import sys
from pathlib import Path

import pytest
from pydantic import BaseModel, TypeAdapter


class VernacularName(BaseModel):
    """Vernacular entry from extractor output."""

    verbatim: str
    canonical: str | None = None


PAIRS_ADAPTER = TypeAdapter(dict[str, list[str | VernacularName]])
SAMPLES_ADAPTER = TypeAdapter(dict[str, list[str]])


@pytest.fixture(scope="session")
def pairs() -> dict[str, list[str | VernacularName]]:
    """Provide extracted pairs data.

    Returns:
        Parsed mapping from latin key to hungarian names.
    """
    return PAIRS_ADAPTER.validate_json(Path(os.environ["PAIRS"]).read_bytes())


@pytest.fixture(scope="session")
def indexed_pairs(pairs: dict[str, list[str | VernacularName]]) -> dict[str, set[str]]:
    """Provide canonical pair index.

    Returns:
        Case-sensitive lookup map over canonical vernacular values.
    """
    index: dict[str, set[str]] = {}
    for latin_name, values in pairs.items():
        latin_casefold = latin_name.casefold()
        existing_values = index.setdefault(latin_casefold, set())
        for value in values:
            if isinstance(value, str):
                existing_values.add(value)
                continue
            existing_values.add(value.canonical or value.verbatim)
    return index


@pytest.fixture(scope="session")
def samples() -> dict[str, list[str]]:
    """Provide expected samples for pairs mode.

    Returns:
        Parsed samples for pair tests.
    """
    samples_path = Path(os.environ["SAMPLES"])
    return SAMPLES_ADAPTER.validate_json(samples_path.read_bytes())


def test_expected_pairs_present(samples: dict[str, list[str]], indexed_pairs: dict[str, set[str]]) -> None:
    """Validate that configured expected pairs match exactly."""
    for latin_name in sorted(samples):
        latin_casefold = latin_name.casefold()
        assert latin_casefold in indexed_pairs, f"Missing extracted key: {latin_name}"
        expected = set(samples[latin_name])
        actual = indexed_pairs[latin_casefold]
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        assert not missing, f"Missing extracted names for {latin_name}: {missing}"
        assert not extra, f"Unexpected extracted names for {latin_name}: {extra}"


if __name__ == "__main__":
    raise SystemExit(pytest.main(sys.argv[1:]))
