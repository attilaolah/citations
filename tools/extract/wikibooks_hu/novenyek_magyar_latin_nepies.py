"""Extract Latin/Hungarian name pairs from Wikibooks Novenyek letter pages."""

import argparse
import json
import re
from pathlib import Path

LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]*))?\]\]")
LATIN_PAREN_LINK_RE = re.compile(r"''\s*\(\s*\[\[([^\]|]+)(?:\|([^\]]*))?\]\]\s*\)\s*''")
LATIN_PAREN_TEXT_RE = re.compile(r"''\s*\(\s*([^()\[\]]+)\s*\)\s*''")
LATIN_TOKEN_RE = re.compile(r"\b[A-Z][A-Za-z-]+(?: [A-Za-z][A-Za-z-]+){0,3}\b")
DASH_SPLIT_RE = re.compile(r"(?<!\w)[\u2013-](?!\w)", re.UNICODE)
OR_SPLIT_RE = re.compile(r"(?:^|\s+)v\.\s+|(?:^|\s+)vagy\s+", re.IGNORECASE)
NOVENYEK_PATH_PARTS_MIN = 3
TAIL_SPLIT_PARTS_MIN = 2
NON_NAME_TAIL_TOKENS = {
    "fokozottan védett",
    "fűszer",
    "védett",
}


def _strip_markup(text: str) -> str:
    cleaned = text
    cleaned = re.sub(r"<ref[^>]*>.*?</ref>", " ", cleaned, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = cleaned.replace("'''", " ")
    cleaned = cleaned.replace("''", " ")
    cleaned = cleaned.replace("&nbsp;", " ")
    cleaned = cleaned.replace("~", " ")
    cleaned = cleaned.replace("|", " ")
    return " ".join(cleaned.split())


def _link_value(target: str, label: str) -> str:
    raw = label or target.rsplit("/", 1)[-1]
    return " ".join(raw.strip().strip("|").split())


def _is_latin_like(value: str) -> bool:
    candidate = " ".join(value.split()).strip().strip(".")
    if not candidate:
        return False
    if re.search(r"[^A-Za-z .-]", candidate):
        return False
    if candidate[0].islower():
        return False
    return LATIN_TOKEN_RE.fullmatch(candidate) is not None


def _first_latin_in_line(line: str) -> str | None:
    candidates: list[str] = []

    for target, label in LATIN_PAREN_LINK_RE.findall(line):
        value = _link_value(target, label)
        candidates.append(value)

    candidates.extend(" ".join(value.split()) for value in LATIN_PAREN_TEXT_RE.findall(line))
    candidates.extend(LATIN_TOKEN_RE.findall(_strip_markup(LINK_RE.sub(" ", line))))

    for candidate in candidates:
        if _is_latin_like(candidate):
            return candidate
    return None


def _is_novenyek_letter_link(target: str) -> bool:
    normalized_target = target
    if target.startswith("NMövények/"):
        normalized_target = "Növények/" + target.removeprefix("NMövények/")
    if not normalized_target.startswith("Növények/"):
        return False
    parts = normalized_target.split("/")
    if len(parts) < NOVENYEK_PATH_PARTS_MIN:
        return False
    letter = parts[1]
    if not letter:
        return False
    if letter in {"Sz", "Zs", "Ö", "Ü", "X,Y"}:
        return True
    return bool(re.fullmatch(r"[A-Z]", letter))


def _names_from_links(line: str, *, letter_links_only: bool) -> list[str]:
    names: list[str] = []
    for target, label in LINK_RE.findall(line):
        if letter_links_only and (not _is_novenyek_letter_link(target)):
            continue
        value = _link_value(target, label)
        if value and (not _is_latin_like(value)):
            names.append(value)
    return names


def _names_from_tail(tail: str) -> list[str]:
    tail = re.sub(r"<ref[^>]*>.*?</ref>", " ", tail, flags=re.IGNORECASE | re.DOTALL)
    tail = _strip_markup(LINK_RE.sub(" ", tail))
    names: list[str] = []
    for chunk in re.split(r"[,;]", tail):
        for part in OR_SPLIT_RE.split(chunk):
            value = " ".join(part.split()).strip(" .:!?()[]{}-'\"")
            # Ignore punctuation-only fragments from malformed wiki markup.
            if (
                value
                and re.search(r"[^\W\d_]", value, flags=re.UNICODE)
                and (not _is_latin_like(value))
                and value.casefold() not in NON_NAME_TAIL_TOKENS
            ):
                names.append(value)
    return names


def _extract_pairs(lines: list[str]) -> dict[str, set[str]]:
    mapping: dict[str, set[str]] = {}

    for raw_line in lines:
        line = raw_line.strip()
        if not line.startswith("*"):
            continue

        latin = _first_latin_in_line(line)
        if latin is None:
            continue

        parts = DASH_SPLIT_RE.split(line, maxsplit=1)
        head = parts[0]
        tail = parts[1] if len(parts) >= TAIL_SPLIT_PARTS_MIN else ""

        head_names = _names_from_links(head, letter_links_only=False)
        tail_link_names = _names_from_links(tail, letter_links_only=True)
        tail_plain_names = _names_from_tail(tail)

        values: set[str] = set(tail_link_names)
        values.update(tail_plain_names)
        # If tail has plain aliases, keep the primary head name as well.
        if tail_plain_names and head_names:
            values.add(head_names[0])
        # If tail contributed nothing useful, fallback to head link names.
        if (not values) and head_names:
            values.update(head_names)
        if not values:
            continue

        mapping.setdefault(latin, set()).update(values)

    return mapping


def _main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    lines = args.input.read_text(encoding="utf-8", errors="replace").splitlines()
    mapping = _extract_pairs(lines)

    sorted_mapping = {
        latin: sorted(values, key=lambda s: s.casefold())
        for latin, values in sorted(mapping.items(), key=lambda kv: kv[0].casefold())
    }

    args.output.write_text(
        json.dumps(sorted_mapping, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
