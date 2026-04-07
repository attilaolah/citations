"""Pytest tests for name-pairs validation."""

import argparse
import os
import sys
from pathlib import Path

import pytest
from pydantic import TypeAdapter

PAIRS_ADAPTER = TypeAdapter(dict[str, list[str]])
PAIRS_PATH_ENV_VAR = "NAME_PAIRS_TEST_PAIRS_PATH"
SAMPLES_PATH_ENV_VAR = "NAME_PAIRS_TEST_SAMPLES_PATH"


def _index_casefolded(pairs: dict[str, list[str]]) -> dict[str, set[str]]:
    index: dict[str, set[str]] = {}
    for latin_name, values in pairs.items():
        latin_casefold = latin_name.casefold()
        existing_values = index.setdefault(latin_casefold, set())
        for value in values:
            existing_values.add(value.casefold())
    return index


@pytest.fixture(scope="session")
def pairs() -> dict[str, list[str]]:
    """Provide extracted pairs data.

    Returns:
        Parsed mapping from latin key to hungarian names.
    """
    return PAIRS_ADAPTER.validate_json(Path(_required_env(PAIRS_PATH_ENV_VAR)).read_bytes())


@pytest.fixture(scope="session")
def indexed_pairs(pairs: dict[str, list[str]]) -> dict[str, set[str]]:
    """Provide casefolded pair index.

    Returns:
        Case-insensitive lookup map.
    """
    return _index_casefolded(pairs)


@pytest.fixture(scope="session")
def samples() -> dict[str, list[str]]:
    """Provide expected samples for pairs mode.

    Returns:
        Parsed samples for pair tests.
    """
    samples_path = Path(_required_env(SAMPLES_PATH_ENV_VAR))
    return PAIRS_ADAPTER.validate_json(samples_path.read_bytes())


def test_expected_pairs_present(
    samples: dict[str, list[str]],
    indexed_pairs: dict[str, set[str]],
) -> None:
    """Validate that configured expected pairs are present."""
    for latin_name in sorted(samples):
        latin_casefold = latin_name.casefold()
        assert latin_casefold in indexed_pairs, f"Missing extracted key: {latin_name}"

        for hungarian_name in sorted(samples[latin_name]):
            hungarian_casefold = hungarian_name.casefold()
            assert (
                hungarian_casefold in indexed_pairs[latin_casefold]
            ), f"Missing extracted pair: {latin_name} = {hungarian_name}"


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pairs", required=True)
    parser.add_argument("--samples", required=True)
    return parser.parse_args(argv)


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if value is None:
        msg = f"Missing required environment variable: {name}"
        raise RuntimeError(msg)
    return value


def _main(argv: list[str]) -> int:
    args = _parse_args(argv)

    previous_pairs = os.environ.get(PAIRS_PATH_ENV_VAR)
    previous_samples = os.environ.get(SAMPLES_PATH_ENV_VAR)
    try:
        os.environ[PAIRS_PATH_ENV_VAR] = args.pairs
        os.environ[SAMPLES_PATH_ENV_VAR] = args.samples
        return pytest.main([__file__])
    finally:
        if previous_pairs is None:
            os.environ.pop(PAIRS_PATH_ENV_VAR, None)
        else:
            os.environ[PAIRS_PATH_ENV_VAR] = previous_pairs
        if previous_samples is None:
            os.environ.pop(SAMPLES_PATH_ENV_VAR, None)
        else:
            os.environ[SAMPLES_PATH_ENV_VAR] = previous_samples


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
