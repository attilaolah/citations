"""Extract Latin/Hungarian name pairs from Wikibooks Novenyek letter pages."""

import argparse
import json
import re
from pathlib import Path

LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]*))?\]\]")
LATIN_PAREN_LINK_RE = re.compile(r"''\s*\(\s*\[\[([^\]|]+)(?:\|([^\]]*))?\]\]\s*\)\s*''")
LATIN_PAREN_TEXT_RE = re.compile(r"''\s*\(\s*([^()\[\]]+)\s*\)\s*''")
LATIN_TOKEN_RE = re.compile(r"\b[A-Z][A-Za-z-]+(?: [A-Za-z][A-Za-z-]+){0,3}\b")
DASH_SPLIT_RE = re.compile(r"\s[\u2013-]\s", re.UNICODE)
NOVENYEK_PATH_PARTS_MIN = 3
TAIL_SPLIT_PARTS_MIN = 2


def _strip_markup(text: str) -> str:
    cleaned = text
    cleaned = re.sub(r"<ref[^>]*>.*?</ref>", " ", cleaned, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = cleaned.replace("''", " ")
    cleaned = cleaned.replace("'''", " ")
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
    if not target.startswith("Növények/"):
        return False
    parts = target.split("/")
    if len(parts) < NOVENYEK_PATH_PARTS_MIN:
        return False
    letter = parts[1]
    if not letter:
        return False
    if letter in {"Sz", "Zs", "Ö", "Ü", "X,Y"}:
        return True
    return bool(re.fullmatch(r"[A-Z]", letter))


def _names_from_links(line: str) -> list[str]:
    names: list[str] = []
    for target, label in LINK_RE.findall(line):
        if _is_novenyek_letter_link(target):
            value = _link_value(target, label)
            if value:
                names.append(value)
    return names


def _names_from_tail(line: str) -> list[str]:
    parts = DASH_SPLIT_RE.split(line, maxsplit=1)
    if len(parts) < TAIL_SPLIT_PARTS_MIN:
        return []

    tail = parts[1]
    tail = re.sub(r"<ref[^>]*>.*?</ref>", " ", tail, flags=re.IGNORECASE | re.DOTALL)
    tail = _strip_markup(LINK_RE.sub(" ", tail))
    names: list[str] = []
    for chunk in re.split(r"[,;]", tail):
        value = " ".join(chunk.split()).strip(" .:!?")
        if value:
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

        values = set(_names_from_links(line))
        values.update(_names_from_tail(line))
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
