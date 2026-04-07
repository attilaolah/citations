"""Extract Latin/Hungarian name pairs from plant_names_in_hungarian HTML tables."""

import argparse
import json
import re
from pathlib import Path

from lxml import html

from tools.extract.known_typos import normalize_known_hungarian_typo

LATIN_ALLOWED_RE = re.compile(r"^[A-Za-z .-]+$")
LATIN_WORD_RE = re.compile(r"^[a-z][a-z-]*$")
LATIN_GENUS_RE = re.compile(r"^[A-Z][a-z-]+$")
RANK_TOKENS = {"subsp", "ssp", "var", "f"}
AGG_TOKENS = {"agg", "agg."}
MIN_COLUMN_COUNT = 3
SINGLE_TOKEN_COUNT = 1
PAIR_TOKEN_COUNT = 2
RANKED_REST_TOKEN_COUNT = 2


def _normalized_text(value: str) -> str:
    return " ".join(value.split())


def _normalized_latin(value: str) -> str | None:
    candidate = _normalized_text(value).strip(" .")
    if not candidate:
        return None
    if LATIN_ALLOWED_RE.fullmatch(candidate) is None:
        return None

    tokens = candidate.split()
    if not tokens:
        return None
    if LATIN_GENUS_RE.fullmatch(tokens[0]) is None:
        return None
    if len(tokens) == SINGLE_TOKEN_COUNT:
        return tokens[0]
    return _normalized_latin_tokens(tokens)


def _normalized_latin_tokens(tokens: list[str]) -> str | None:
    species = tokens[1]
    if LATIN_WORD_RE.fullmatch(species) is None:
        return None
    if len(tokens) == PAIR_TOKEN_COUNT:
        return f"{tokens[0]} {species}"
    return _normalize_latin_rest(tokens[0], species, tokens[2:])


def _normalize_latin_rest(genus: str, species: str, rest: list[str]) -> str | None:
    if len(rest) == 1 and rest[0] in AGG_TOKENS:
        return f"{genus} {species} agg"

    if (
        len(rest) == RANKED_REST_TOKEN_COUNT
        and rest[0].removesuffix(".") in RANK_TOKENS
        and LATIN_WORD_RE.fullmatch(rest[1])
    ):
        rank = rest[0].removesuffix(".")
        return f"{genus} {species} {rank}. {rest[1]}"

    if all(LATIN_WORD_RE.fullmatch(token) for token in rest):
        return " ".join([genus, species, *rest])

    return None


def _extract_pairs(content: bytes) -> dict[str, set[str]]:
    if not content.strip():
        return {}

    document = html.fromstring(content)
    mapping: dict[str, set[str]] = {}

    for row in document.xpath("//tr[td]"):
        columns = row.xpath("./td")
        if len(columns) < MIN_COLUMN_COUNT:
            continue

        hungarian = normalize_known_hungarian_typo(_normalized_text(columns[1].text_content()))
        latin = _normalized_latin(columns[2].text_content())
        if not hungarian or not latin:
            continue

        mapping.setdefault(latin, set()).add(hungarian)

    return mapping


def _main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    mapping = _extract_pairs(args.input.read_bytes())
    sorted_mapping = {
        latin: sorted(values, key=lambda value: value.casefold())
        for latin, values in sorted(mapping.items(), key=lambda item: item[0].casefold())
    }

    args.output.write_text(
        json.dumps(sorted_mapping, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
