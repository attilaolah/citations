"""Pytest tests for name-pairs validation."""

import argparse
import os
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import TypeAdapter

PAIRS_ADAPTER: TypeAdapter[dict[str, list[str]]] = TypeAdapter(dict[str, list[str]])
GNPARSER_OUTPUT_ADAPTER: TypeAdapter[dict[str, object]] = TypeAdapter(dict[str, object])

MODE_ENV_VAR = "NAME_PAIRS_TEST_MODE"
PAIRS_PATH_ENV_VAR = "NAME_PAIRS_TEST_PAIRS_PATH"
SAMPLES_PATH_ENV_VAR = "NAME_PAIRS_TEST_SAMPLES_PATH"
GNPARSER_PATH_ENV_VAR = "NAME_PAIRS_TEST_GNPARSER_PATH"


def _index_casefolded(pairs: dict[str, list[str]]) -> dict[str, set[str]]:
    index: dict[str, set[str]] = {}
    for latin_name, values in pairs.items():
        latin_casefold = latin_name.casefold()
        existing_values = index.setdefault(latin_casefold, set())
        for value in values:
            existing_values.add(value.casefold())
    return index


def _normalize_gnparser_candidate(name: str) -> str:
    return name.title() if name.isupper() else name


@pytest.fixture(scope="session")
def mode() -> str:
    """Provide selected test mode.

    Returns:
        Active test mode from macro-provided environment.
    """
    return _required_env(MODE_ENV_VAR)


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
def samples(mode: str) -> dict[str, list[str]] | None:
    """Provide expected samples for pairs mode.

    Returns:
        Parsed samples for pair tests, otherwise `None`.
    """
    if mode != "pairs":
        return None

    samples_path = Path(_required_env(SAMPLES_PATH_ENV_VAR))
    return PAIRS_ADAPTER.validate_json(samples_path.read_bytes())


@pytest.fixture(scope="session")
def gnparser_bin(mode: str) -> Path | None:
    """Provide gnparser binary in gnparser mode.

    Returns:
        Path to gnparser binary, otherwise `None`.
    """
    if mode != "gnparser":
        return None
    return Path(_required_env(GNPARSER_PATH_ENV_VAR))


def test_expected_pairs_present(
    mode: str,
    samples: dict[str, list[str]] | None,
    indexed_pairs: dict[str, set[str]],
) -> None:
    """Validate that configured expected pairs are present."""
    if mode != "pairs" or samples is None:
        return

    for latin_name in sorted(samples):
        latin_casefold = latin_name.casefold()
        assert latin_casefold in indexed_pairs, f"Missing extracted key: {latin_name}"

        for hungarian_name in sorted(samples[latin_name]):
            hungarian_casefold = hungarian_name.casefold()
            assert (
                hungarian_casefold in indexed_pairs[latin_casefold]
            ), f"Missing extracted pair: {latin_name} = {hungarian_name}"


def test_gnparser_matches_all_keys(
    mode: str,
    pairs: dict[str, list[str]],
    gnparser_bin: Path | None,
) -> None:
    """Validate that every extracted key is parseable by gnparser."""
    if mode != "gnparser" or gnparser_bin is None:
        return

    failures: list[tuple[str, str, str, str]] = []

    for key in sorted(pairs):
        candidate = _normalize_gnparser_candidate(key)
        proc = subprocess.run(
            [str(gnparser_bin), candidate, "-f", "compact"],
            check=False,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            failures.append((key, candidate, "non-zero exit", proc.stderr.strip()))
            continue

        output = proc.stdout.strip()
        parsed = GNPARSER_OUTPUT_ADAPTER.validate_json(output)
        if parsed.get("parsed") is not True:
            failures.append((key, candidate, "no parse match", output))

    assert not failures, "gnparser validation failures:\n" + "\n".join(
        f"key={key!r} candidate={candidate!r} reason={reason} details={details}"
        for key, candidate, reason, details in failures
    )


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["pairs", "gnparser"], required=True)
    parser.add_argument("--pairs", required=True)
    parser.add_argument("--samples")
    parser.add_argument("--gnparser")
    return parser.parse_args(argv)


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if value is None:
        msg = f"Missing required environment variable: {name}"
        raise RuntimeError(msg)
    return value


def _main(argv: list[str]) -> int:
    args = _parse_args(argv)
    if args.mode == "pairs" and args.samples is None:
        msg = "--samples is required when --mode=pairs"
        raise ValueError(msg)
    if args.mode == "gnparser" and args.gnparser is None:
        msg = "--gnparser is required when --mode=gnparser"
        raise ValueError(msg)

    env = dict(os.environ)
    env[MODE_ENV_VAR] = args.mode
    env[PAIRS_PATH_ENV_VAR] = args.pairs
    if args.samples is not None:
        env[SAMPLES_PATH_ENV_VAR] = args.samples
    if args.gnparser is not None:
        env[GNPARSER_PATH_ENV_VAR] = args.gnparser
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", __file__],
        check=False,
        env=env,
    )
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
