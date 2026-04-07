"""Pytest tests for name-pairs validation."""

import os
import sys
from pathlib import Path

import pytest
from pydantic import TypeAdapter

PAIRS_ADAPTER = TypeAdapter(dict[str, list[str]])


@pytest.fixture(scope="session")
def pairs() -> dict[str, list[str]]:
    """Provide extracted pairs data.

    Returns:
        Parsed mapping from latin key to hungarian names.
    """
    return PAIRS_ADAPTER.validate_json(Path(os.environ["PAIRS_PATH"]).read_bytes())


@pytest.fixture(scope="session")
def indexed_pairs(pairs: dict[str, list[str]]) -> dict[str, set[str]]:
    """Provide casefolded pair index.

    Returns:
        Case-insensitive lookup map.
    """
    index: dict[str, set[str]] = {}
    for latin_name, values in pairs.items():
        latin_casefold = latin_name.casefold()
        existing_values = index.setdefault(latin_casefold, set())
        for value in values:
            existing_values.add(value.casefold())
    return index


@pytest.fixture(scope="session")
def samples() -> dict[str, list[str]]:
    """Provide expected samples for pairs mode.

    Returns:
        Parsed samples for pair tests.
    """
    samples_path = Path(os.environ["SAMPLES_PATH"])
    return PAIRS_ADAPTER.validate_json(samples_path.read_bytes())


def test_expected_pairs_present(samples: dict[str, list[str]], indexed_pairs: dict[str, set[str]]) -> None:
    """Validate that configured expected pairs are present."""
    for latin_name in sorted(samples):
        latin_casefold = latin_name.casefold()
        assert latin_casefold in indexed_pairs, f"Missing extracted key: {latin_name}"

        for hungarian_name in sorted(samples[latin_name]):
            hungarian_casefold = hungarian_name.casefold()
            assert (
                hungarian_casefold in indexed_pairs[latin_casefold]
            ), f"Missing extracted pair: {latin_name} = {hungarian_name}"


if __name__ == "__main__":
    raise SystemExit(pytest.main(sys.argv[1:]))
