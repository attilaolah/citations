"""Create cleaned name-pairs output using gnparser."""

import json
import subprocess
from collections.abc import Callable
from os import EX_OK
from pathlib import Path  # NOQA: TC003

from pydantic import BaseModel, FilePath, TypeAdapter

from tools.extract.known_typos import normalize_hungarian_light_canonical
from tools.settings import IOSettings


class VernacularName(BaseModel):
    """Vernacular entry from extractor output."""

    verbatim: str
    canonical: str | None = None


class _Settings(IOSettings):
    gnparser: FilePath


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
            values.append(
                {
                    "canonical": normalize_hungarian_light_canonical(value),
                    "verbatim": value,
                },
            )
            continue

        canonical_input = value.canonical or value.verbatim
        values.append(
            {
                "canonical": normalize_hungarian_light_canonical(canonical_input),
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


def _main() -> int:
    settings = _Settings.from_args()
    pairs = PAIRS_ADAPTER.validate_json(settings.input.read_bytes())

    cleaned_entries: list[dict[str, object]] = [
        _clean_entry(_run_gnparser(settings.gnparser, key), pairs[key]) for key in sorted(pairs)
    ]

    settings.output.write_text(
        json.dumps(cleaned_entries, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return EX_OK


if __name__ == "__main__":
    raise SystemExit(_main())
