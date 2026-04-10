"""Create cleaned name-pairs output using gnparser."""

import json
from collections.abc import Callable
from os import EX_OK
from typing import TYPE_CHECKING

from pydantic import FilePath, RootModel

from tools.extract.known_typos import normalize_hungarian_light_canonical
from tools.extract.models import PAIRS_ADAPTER, VernacularName
from tools.extract.process import run_json_tool
from tools.settings import IOSettings

if TYPE_CHECKING:
    from pathlib import Path


class _Settings(IOSettings):
    gnparser: FilePath


class _GNParserOutput(RootModel[dict[str, object]]):
    """Compact gnparser output payload."""


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
    parsed = run_json_tool(
        argv=[str(gnparser_bin), candidate, "--format", "compact"],
        context=f"gnparser failed for key={key!r} candidate={candidate!r}",
        model=_GNParserOutput,
    )
    output = parsed.root
    if output.get("parsed") is not True:
        msg = f"gnparser did not parse key={key!r} candidate={candidate!r}: {output!r}"
        raise RuntimeError(msg)
    return output


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
