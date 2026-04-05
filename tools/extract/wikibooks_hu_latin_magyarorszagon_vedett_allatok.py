"""Extract Latin/Hungarian name pairs from one specific Wikibooks raw page."""

import argparse
import json
import re
from pathlib import Path

LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]*))?\]\]")
PAREN_RE = re.compile(r"\(([^)]*)\)")
QUOTE_PAREN_RE = re.compile(r"''\(([^)]*)\)''")

# Examples in this document: Acridoidea, Plecoptera, Insecta, Mantis religiosa
LATIN_TOKEN_RE = re.compile(r"\b[A-Z][A-Za-z-]+(?: [a-z][a-z-]+)?\b")
MIN_TABLE_CELLS = 2
MULTI_LINK_CELL = 2
THREE_CELL_ROW = 3


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


def _parse_table_row(line: str) -> list[tuple[str, str]]:
    cells = _split_table_cells(line)
    if not cells:
        return []

    pairs = _parse_concat_first_cell(cells)
    if pairs:
        return pairs

    pairs = _parse_empty_first_column(cells)
    if pairs:
        return pairs

    return _parse_standard_cells(cells)


def _split_table_cells(line: str) -> list[str]:
    content = line[1:].strip()
    if "||" not in content:
        return []

    cells = [cell.strip() for cell in content.split("||")]
    if len(cells) < MIN_TABLE_CELLS:
        return []
    return cells


def _parse_concat_first_cell(cells: list[str]) -> list[tuple[str, str]]:
    left_links = _extract_link_texts(cells[0])
    right_links = _extract_link_texts(cells[1])
    right_name = right_links[0] if right_links else _strip_markup(cells[1])
    if len(left_links) < MULTI_LINK_CELL or right_name:
        return []

    latin_links = [value for value in left_links if _is_latin_like(value)]
    hungarian_links = [value for value in left_links if not _is_latin_like(value)]
    if not latin_links or not hungarian_links:
        return []
    return [(latin_links[0], hungarian_links[0])]


def _parse_empty_first_column(cells: list[str]) -> list[tuple[str, str]]:
    if len(cells) < THREE_CELL_ROW or _strip_markup(cells[0]):
        return []

    c1_links = _extract_link_texts(cells[1])
    c2_links = _extract_link_texts(cells[2])
    c1_text = c1_links[0] if c1_links else _strip_markup(cells[1])
    c2_text = c2_links[0] if c2_links else _strip_markup(cells[2])
    c1_latin = _first_latin_candidate(c1_links) or _first_latin_candidate(LATIN_TOKEN_RE.findall(c1_text))
    c2_latin = _first_latin_candidate(c2_links) or _first_latin_candidate(LATIN_TOKEN_RE.findall(c2_text))
    if c1_latin is not None and not _is_latin_like(c2_text):
        return [(c1_latin, c2_text)]
    if c2_latin is not None and not _is_latin_like(c1_text):
        return [(c2_latin, c1_text)]
    return []


def _parse_standard_cells(cells: list[str]) -> list[tuple[str, str]]:
    left_links = _extract_link_texts(cells[0])
    right_links = _extract_link_texts(cells[1])
    left_name = left_links[0] if left_links else _strip_markup(cells[0])
    right_name = right_links[0] if right_links else _strip_markup(cells[1])
    left_hungarian_names = _extract_hungarian_names(cells[0])

    if not left_name or not right_name:
        return []
    if {left_name, right_name} == {"Magyar neve", "Latin neve"}:
        return []

    right_latin = _first_latin_candidate(right_links)
    if right_latin is None:
        right_latin = _first_latin_candidate(LATIN_TOKEN_RE.findall(_strip_markup(cells[1])))
    if right_latin is not None:
        names = left_hungarian_names or [left_name]
        return [(right_latin, name) for name in names]

    latin_candidates = [link for link in left_links if _is_latin_like(link)]
    latin_candidates.extend(LATIN_TOKEN_RE.findall(_strip_markup(cells[0])))

    pairs: list[tuple[str, str]] = []
    seen_latin: set[str] = set()
    for latin in latin_candidates:
        if not _is_latin_like(latin) or latin in seen_latin:
            continue
        seen_latin.add(latin)
        pairs.append((latin, right_name))
    return pairs


def _extract_hungarian_names(cell: str) -> list[str]:
    names: list[str] = list(_extract_link_texts(cell))

    cleaned = _strip_markup(LINK_RE.sub(" ", cell))
    for part in re.split(r"\s+vagy\s+", cleaned):
        candidate = " ".join(part.split()).strip(" ,;|")
        candidate = re.sub(r"^vagy\s+", "", candidate, flags=re.IGNORECASE)
        candidate = re.sub(r"\s+vagy$", "", candidate, flags=re.IGNORECASE)
        if candidate.casefold() == "vagy":
            continue
        if candidate:
            names.append(candidate)

    unique: list[str] = []
    seen: set[str] = set()
    for name in names:
        if name in seen:
            continue
        seen.add(name)
        unique.append(name)
    return unique


def _parse_taxon_bullet(line: str) -> tuple[str, str] | None:
    if not re.match(r"^[*;'\s]+", line):
        return None

    body = re.sub(r"^[*;'\s]+", "", line).strip()
    links = _extract_link_texts(body)

    hungarian = links[0] if links else _strip_markup(PAREN_RE.sub("", body))
    hungarian = hungarian.strip()
    if not hungarian:
        return None
    latin_candidates: list[str] = []
    latin_candidates.extend(_strip_markup(match) for match in QUOTE_PAREN_RE.findall(body))
    latin_candidates.extend(_strip_markup(match) for match in PAREN_RE.findall(body))
    latin_candidates.extend(LATIN_TOKEN_RE.findall(_strip_markup(LINK_RE.sub(" ", body))))
    latin = _first_latin_candidate(latin_candidates)
    if latin is None:
        return None
    return latin, hungarian


def _extract_pairs(lines: list[str]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for raw_line in lines:
        line = raw_line.strip()
        pair: tuple[str, str] | None = None

        if line.startswith("=") and line.endswith("="):
            pair = _parse_heading(line)
        elif line.startswith(("|", "!")):
            table_pairs = _parse_table_row(line)
            for table_pair in table_pairs:
                if table_pair in seen:
                    continue
                seen.add(table_pair)
                pairs.append(table_pair)
            continue
        elif re.match(r"^[*;']+", line):
            pair = _parse_taxon_bullet(line)

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

    mapping: dict[str, set[str]] = {}
    for latin, hungarian in pairs:
        mapping.setdefault(latin, set()).add(hungarian)

    sorted_mapping = {latin: sorted(mapping[latin]) for latin in sorted(mapping)}
    args.output.write_text(
        json.dumps(sorted_mapping, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
