"""Create cleaned name-pairs output using gnparser."""

import argparse
import json
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

from pydantic import BaseModel, TypeAdapter


class VernacularName(BaseModel):
    """Vernacular entry from extractor output."""

    verbatim: str
    canonical: str | None = None


PAIRS_ADAPTER = TypeAdapter(dict[str, list[str | VernacularName]])
GNPARSER_OUTPUT_ADAPTER = TypeAdapter(dict[str, object])

_DROP_FIELDS = {
    "id",
    "parsed",
    "parsedVersion",
    "parserVersion",
}

CleanStep = Callable[[dict[str, object], list[str | VernacularName]], dict[str, object]]


def _normalize_gnparser_candidate(name: str) -> str:
    return name.title() if name.isupper() else name


def _run_gnparser(gnparser_bin: Path, key: str) -> dict[str, object]:
    candidate = _normalize_gnparser_candidate(key)
    proc = subprocess.run(
        [str(gnparser_bin), candidate, "--format", "compact"],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        msg = f"gnparser failed for key={key!r} candidate={candidate!r}: {proc.stderr.strip()}"
        raise RuntimeError(msg)

    parsed = GNPARSER_OUTPUT_ADAPTER.validate_json(proc.stdout)
    if parsed.get("parsed") is not True:
        msg = f"gnparser did not parse key={key!r} candidate={candidate!r}: {proc.stdout.strip()}"
        raise RuntimeError(msg)
    return parsed


def _drop_gnparser_fields(entry: dict[str, object], _: list[str | VernacularName]) -> dict[str, object]:
    return {key: value for key, value in entry.items() if key not in _DROP_FIELDS}


def _add_hungarian_vernacular(
    entry: dict[str, object],
    vernaculars: list[str | VernacularName],
) -> dict[str, object]:
    out = dict(entry)
    out["vernacular"] = {
        "hu": _normalized_vernacular_output(vernaculars),
    }
    return out


def _normalized_vernacular_output(vernaculars: list[str | VernacularName]) -> list[dict[str, str]]:
    values: list[dict[str, str]] = []
    for value in vernaculars:
        if isinstance(value, str):
            values.append({"canonical": value, "verbatim": value})
            continue

        values.append(
            {
                "canonical": value.canonical or value.verbatim,
                "verbatim": value.verbatim,
            },
        )
    return values


def _clean_entry(raw: dict[str, object], vernaculars: list[str | VernacularName]) -> dict[str, object]:
    # Cleaning is a small pipeline so additional steps can be inserted later.
    steps: list[CleanStep] = [
        _drop_gnparser_fields,
        _add_hungarian_vernacular,
    ]
    entry = raw
    for step in steps:
        entry = step(entry, vernaculars)
    return entry


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--gnparser", required=True)
    return parser.parse_args(argv)


def _main(argv: list[str]) -> int:
    args = _parse_args(argv)
    pairs = PAIRS_ADAPTER.validate_json(Path(args.input).read_bytes())

    gnparser_bin = Path(args.gnparser)

    cleaned_entries: list[dict[str, object]] = [
        _clean_entry(_run_gnparser(gnparser_bin, key), pairs[key]) for key in sorted(pairs)
    ]

    Path(args.output).write_text(
        json.dumps(cleaned_entries, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
