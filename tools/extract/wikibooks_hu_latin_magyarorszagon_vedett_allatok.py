"""Extract Latin/Hungarian name pairs from one specific Wikibooks raw page."""

import argparse
import re
from pathlib import Path

LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]*))?\]\]")
PAREN_RE = re.compile(r"\(([^)]*)\)")
QUOTE_PAREN_RE = re.compile(r"''\(([^)]*)\)''")

# Examples in this document: Acridoidea, Plecoptera, Insecta, Mantis religiosa
LATIN_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z-]*(?: [a-z][a-z-]*)?")
MIN_TABLE_CELLS = 2


def _strip_markup(text: str) -> str:
    cleaned = text
    cleaned = cleaned.replace("''", " ")
    cleaned = cleaned.replace("<center>", " ").replace("</center>", " ")
    cleaned = cleaned.replace("<big>", " ").replace("</big>", " ")
    cleaned = cleaned.replace("<b>", " ").replace("</b>", " ")
    cleaned = cleaned.replace("<nowiki>", " ").replace("</nowiki>", " ")
    cleaned = cleaned.replace("&nbsp;", " ")
    cleaned = cleaned.replace("|", " ")
    return " ".join(cleaned.split())


def _extract_link_texts(text: str) -> list[str]:
    out: list[str] = []
    for target, label in LINK_RE.findall(text):
        raw = label or target.rsplit("/", 1)[-1]
        value = raw.strip().strip("|").strip()
        if value:
            out.append(value)
    return out


def _is_latin_like(value: str) -> bool:
    candidate = " ".join(value.split()).strip()
    if not candidate:
        return False
    if re.search(r"[^A-Za-z -]", candidate):
        return False
    if candidate[0].islower():
        return False
    return LATIN_TOKEN_RE.fullmatch(candidate) is not None


def _first_latin_candidate(values: list[str]) -> str | None:
    for value in values:
        candidate = " ".join(value.split()).strip().strip("|")
        if _is_latin_like(candidate):
            return candidate
    return None


def _parse_heading(line: str) -> tuple[str, str] | None:
    body = re.sub(r"^=+\s*", "", line)
    body = re.sub(r"\s*=+$", "", body).strip()

    links = _extract_link_texts(body)
    if not links:
        return None

    hungarian = links[0]

    latin_values = list(links[1:])
    latin_values.extend(_strip_markup(match) for match in QUOTE_PAREN_RE.findall(body))
    latin_values.extend(_strip_markup(match) for match in PAREN_RE.findall(body))

    residual = _strip_markup(LINK_RE.sub(" ", body))
    latin_values.extend(LATIN_TOKEN_RE.findall(residual))

    latin = _first_latin_candidate(latin_values)
    if latin is None:
        return None
    return latin, hungarian


def _parse_table_row(line: str) -> tuple[str, str] | None:
    content = line[1:].strip()
    if "||" not in content:
        return None

    cells = [cell.strip() for cell in content.split("||")]
    if len(cells) < MIN_TABLE_CELLS:
        return None

    left_links = _extract_link_texts(cells[0])
    right_links = _extract_link_texts(cells[1])
    left_name = left_links[0] if left_links else _strip_markup(cells[0])
    right_name = right_links[0] if right_links else _strip_markup(cells[1])

    if not left_name or not right_name:
        return None

    right_latin = _first_latin_candidate(right_links)
    if right_latin is None:
        right_latin = _first_latin_candidate(LATIN_TOKEN_RE.findall(_strip_markup(cells[1])))
    if right_latin is not None:
        return right_latin, left_name

    left_latin = _first_latin_candidate(left_links)
    if left_latin is None:
        left_latin = _first_latin_candidate(LATIN_TOKEN_RE.findall(_strip_markup(cells[0])))
    if left_latin is None:
        return None

    return left_latin, right_name


def _extract_pairs(lines: list[str]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for raw_line in lines:
        line = raw_line.strip()
        pair: tuple[str, str] | None = None

        if line.startswith("=") and line.endswith("="):
            pair = _parse_heading(line)
        elif line.startswith(("|", "!")):
            pair = _parse_table_row(line)

        if pair is None:
            continue
        if pair in seen:
            continue

        seen.add(pair)
        pairs.append(pair)

    return pairs


def _main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    lines = args.input.read_text(encoding="utf-8", errors="replace").splitlines()
    pairs = _extract_pairs(lines)

    args.output.write_text(
        "\n".join(f"{latin} = {hungarian}" for latin, hungarian in pairs) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
