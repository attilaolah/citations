"""Extract Latin/Hungarian name pairs from Wikibooks Novenyek letter pages."""

import argparse
import json
import operator
import re
import unicodedata
from itertools import starmap
from pathlib import Path

LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]*))?\]\]")
LATIN_PAREN_LINK_RE = re.compile(r"''\s*\(\s*\[\[([^\]|]+)(?:\|([^\]]*))?\]\]\s*\)\s*''")
LATIN_PAREN_LINK_BROKEN_RE = re.compile(r"''\s*\(\s*\[\[([^\]|]+)(?:\|([^\]]*))?\]\]\s*''")
LATIN_PAREN_TEXT_RE = re.compile(r"''\s*\(\s*([^()\[\]]+)\s*\)\s*''")
LATIN_PHRASE_RE = re.compile(r"\b[A-Z][A-Za-z-]+(?: [A-Za-z][A-Za-z-]+){1,3}\b")
RANKED_LATIN_PHRASE_RE = re.compile(
    r"\b[A-Z][A-Za-z-]+ [a-z][a-z-]+ (?:subsp|subsp\.|ssp|ssp\.|var|var\.|f|f\.) [a-z][a-z-]+\b",
)
PAREN_GENUS_SYNONYM_RE = re.compile(r"\b([A-Z][A-Za-z-]+)\s*\(([A-Z][A-Za-z-]+)\)\s*([a-z][A-Za-z-]+)\b")
GENERIC_PAREN_RE = re.compile(r"\(([^)]{2,})\)")
ASCII_TOKEN_RE = re.compile(r"[A-Za-z]+(?:-[A-Za-z]+)*")
LATIN_RANK_MARKERS = {"subsp", "subsp.", "ssp", "ssp.", "var", "var.", "f", "f.", "cf", "cf."}
DASH_SPLIT_RE = re.compile(r"(?<!\w)[\u2013-](?!\w)", re.UNICODE)
OR_SPLIT_RE = re.compile(r"(?:^|\s+)v\.\s+|(?:^|\s+)vagy\s+", re.IGNORECASE)
NOVENYEK_PATH_PARTS_MIN = 3
TAIL_SPLIT_PARTS_MIN = 2
MIN_LATIN_PARTS = 2
NON_NAME_TAIL_TOKENS = {
    "fokozottan védett",
    "fűszer",
    "védett",
}
NON_ORGANISM_SUFFIXES = {"anthodium", "flos", "fructus", "herba", "radix", "semen"}
FORBIDDEN_LATIN_LAST_TOKENS = {"flos", "radix"}
LATIN_SEPARATOR_TOKENS = {"es", "illetve", "syn", "vagy", "és"}
WORD_TOKEN_RE = re.compile(r"^[^\W\d_]+(?:-[^\W\d_]+)*$", re.UNICODE)
PAIR_WITH_HEAD_RE = re.compile(
    r"^\s*(?P<left>[^\W\d_]+(?:-[^\W\d_]+)*)\s+vagy\s+"
    r"(?P<alt>[^\W\d_]+(?:-[^\W\d_]+)*)\s+(?P<head>[^\W\d_]+(?:-[^\W\d_]+)*)\s*$",
    flags=re.IGNORECASE | re.UNICODE,
)
PAIR_OR_RE = re.compile(
    r"^\s*(?P<left>[^\W\d_]+(?:-[^\W\d_]+)*)\s+vagy\s+(?P<right>[^\W\d_]+(?:-[^\W\d_]+)*)\s*$",
    flags=re.IGNORECASE | re.UNICODE,
)
PLANT_SUFFIXES = ("fa",)
LEVENSHTEIN_MAX_DISTANCE = 2


def _strip_markup(text: str) -> str:
    cleaned = text
    cleaned = cleaned.replace("[[[", "[[").replace("]]]", "]]")
    cleaned = re.sub(r"\(\[\[([^\]|()]+)\)", r"([[\1]])", cleaned)
    cleaned = re.sub(r"\(([^()\[\]|]+)\]\]", r"([[\1]])", cleaned)
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


def _replace_links_with_values(text: str) -> str:
    return LINK_RE.sub(lambda match: f" {_link_value(match.group(1), match.group(2))} ", text)


def _is_latin_like(value: str) -> bool:
    normalized = _normalize_latin_candidate(value)
    if normalized is None:
        return False
    candidate = " ".join(normalized.split()).strip().strip(".")
    if not candidate:
        return False
    parts = candidate.split()
    if len(parts) < MIN_LATIN_PARTS:
        return False
    if parts[0][0].islower() or (ASCII_TOKEN_RE.fullmatch(parts[0]) is None):
        return False
    for part in parts[1:]:
        if part.casefold() in LATIN_RANK_MARKERS:
            continue
        part_ascii = "".join(
            char for char in unicodedata.normalize("NFKD", part.casefold()) if not unicodedata.combining(char)
        )
        if ASCII_TOKEN_RE.fullmatch(part_ascii) is None:
            return False
    return True


def _ascii_fold(value: str) -> str:
    return "".join(char for char in unicodedata.normalize("NFKD", value) if not unicodedata.combining(char))


def _tokenize_latin_candidate(raw: str) -> list[str]:
    cleaned = _strip_markup(raw)
    cleaned = re.sub(r"[\[\]{}|()]", " ", cleaned)
    cleaned = " ".join(cleaned.split())
    if not cleaned:
        return []
    tokens = [token.strip(".,;:!?\"'`") for token in cleaned.split()]
    return [token for token in tokens if token]


def _find_genus_index(tokens: list[str]) -> int:
    for index, token in enumerate(tokens):
        if re.fullmatch(r"[A-Z][a-z-]+", token):
            return index
    return -1


def _append_latin_token(latin_tokens: list[str], token: str) -> bool:
    appended = False

    if re.fullmatch(r"[A-Z][a-z-]{3,}", token) and len(latin_tokens) == 1:
        latin_tokens.append(token.casefold())
        appended = True
    else:
        if re.fullmatch(r"[A-Z][a-z-]+\.?", token) and len(latin_tokens) >= MIN_LATIN_PARTS:
            return False
        token_folded_ascii = _ascii_fold(token.casefold())
        if token_folded_ascii in LATIN_SEPARATOR_TOKENS:
            return False
        if re.fullmatch(r"[a-z-]+", token_folded_ascii) is None and token_folded_ascii not in LATIN_RANK_MARKERS:
            return False

        if token_folded_ascii in LATIN_RANK_MARKERS:
            latin_tokens.append(token_folded_ascii if token.endswith(".") else token_folded_ascii.removesuffix("."))
            appended = True
        elif token_folded_ascii in NON_ORGANISM_SUFFIXES:
            appended = False
        elif ASCII_TOKEN_RE.fullmatch(token_folded_ascii) and token_folded_ascii[0].islower():
            latin_tokens.append(token_folded_ascii)
            appended = True

    return appended


def _normalize_latin_candidate(raw: str) -> str | None:
    tokens = _tokenize_latin_candidate(raw)
    if not tokens:
        return None

    genus_index = _find_genus_index(tokens)
    if genus_index < 0:
        return None

    latin_tokens = [tokens[genus_index]]
    for token in tokens[genus_index + 1 :]:
        if not _append_latin_token(latin_tokens, token):
            break

    if len(latin_tokens) < MIN_LATIN_PARTS:
        return None
    if latin_tokens[-1].casefold() in FORBIDDEN_LATIN_LAST_TOKENS:
        return None
    return " ".join(latin_tokens)


def _collect_normalized_candidates(values: list[str]) -> list[str]:
    candidates: list[str] = []
    for value in values:
        normalized = _normalize_latin_candidate(value)
        if normalized:
            candidates.append(normalized)
    return candidates


def _expand_parenthetical_genus_synonyms(values: list[str]) -> list[str]:
    expanded: list[str] = []
    for value in values:
        match = PAREN_GENUS_SYNONYM_RE.fullmatch(" ".join(value.split()))
        if match is None:
            continue
        outer_genus, inner_genus, species = match.groups()
        expanded.extend([f"{outer_genus} {species}", f"{inner_genus} {species}"])
    return expanded


def _dedupe(values: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _latin_candidates_in_line(line: str) -> list[str]:
    link_values = list(starmap(_link_value, LATIN_PAREN_LINK_RE.findall(line)))
    link_values.extend(starmap(_link_value, LATIN_PAREN_LINK_BROKEN_RE.findall(line)))
    link_values += _expand_parenthetical_genus_synonyms(link_values)
    text_values = LATIN_PAREN_TEXT_RE.findall(line)
    generic_values = GENERIC_PAREN_RE.findall(line)
    phrase_values = LATIN_PHRASE_RE.findall(_strip_markup(LINK_RE.sub(" ", line)))
    ranked_phrase_values = RANKED_LATIN_PHRASE_RE.findall(_strip_markup(LINK_RE.sub(" ", line)))
    paren_genus_synonyms: list[str] = []
    for outer_genus, inner_genus, species in PAREN_GENUS_SYNONYM_RE.findall(_strip_markup(LINK_RE.sub(" ", line))):
        paren_genus_synonyms.extend([f"{outer_genus} {species}", f"{inner_genus} {species}"])
    combined = (
        _collect_normalized_candidates(link_values)
        + _collect_normalized_candidates(text_values)
        + _collect_normalized_candidates(generic_values)
        + _collect_normalized_candidates(phrase_values)
        + _collect_normalized_candidates(ranked_phrase_values)
        + _collect_normalized_candidates(paren_genus_synonyms)
    )
    return _dedupe(combined)


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


def _names_from_links(line: str, *, letter_links_only: bool, exclude_latin_like: bool = True) -> list[str]:
    names: list[str] = []
    for target, label in LINK_RE.findall(line):
        if letter_links_only and (not _is_novenyek_letter_link(target)):
            continue
        value = _link_value(target, label)
        if value and ((not exclude_latin_like) or (not _is_latin_like(value))):
            names.append(value)
    return names


def _names_from_tail(tail: str) -> list[str]:
    tail = re.sub(r"<ref[^>]*>.*?</ref>", " ", tail, flags=re.IGNORECASE | re.DOTALL)
    tail = _strip_markup(_replace_links_with_values(tail))
    chunks = [part for part in (_clean_tail_fragment(part) for part in re.split(r"[,;]", tail)) if part]
    grouped_names, consumed_indexes = _expand_prefix_grouping(chunks)
    names = list(grouped_names)
    for index, chunk in enumerate(chunks):
        if index in consumed_indexes:
            continue
        names.extend(_names_from_chunk(chunk))
    return names


def _clean_tail_fragment(value: str) -> str:
    cleaned = " ".join(value.split()).strip(" .:!?()[]{}-'\"")
    return re.sub(r"^(?:fokozottan\s+)?védett!?\s*[-\u2013]\s*", "", cleaned, flags=re.IGNORECASE)


def _expand_prefix_grouping(chunks: list[str]) -> tuple[list[str], set[int]]:
    names: list[str] = []
    consumed_indexes: set[int] = set()
    for index in range(len(chunks) - 1):
        if index in consumed_indexes or (index + 1) in consumed_indexes:
            continue
        prefix = chunks[index]
        if not _is_single_word(prefix):
            continue
        pair_match = PAIR_WITH_HEAD_RE.fullmatch(chunks[index + 1])
        if pair_match is None:
            continue
        left = pair_match.group("left")
        alt = pair_match.group("alt")
        head = pair_match.group("head")
        names.extend([f"{prefix} {head}", f"{left} {head}", f"{alt} {head}"])
        consumed_indexes.update({index, index + 1})
    return names, consumed_indexes


def _names_from_chunk(chunk: str) -> list[str]:
    pair_match = PAIR_OR_RE.fullmatch(chunk)
    if pair_match is not None:
        maybe_expanded = _expand_vagy_pair_suffix(pair_match.group("left"), pair_match.group("right"))
        if maybe_expanded is not None:
            return maybe_expanded

    names: list[str] = []
    for part in OR_SPLIT_RE.split(chunk):
        value = _clean_tail_fragment(part)
        if _is_acceptable_vernacular(value):
            names.append(value)
    return names


def _is_single_word(value: str) -> bool:
    return WORD_TOKEN_RE.fullmatch(value) is not None


def _levenshtein_distance(left: str, right: str) -> int:
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)

    previous = list(range(len(right) + 1))
    for i, left_char in enumerate(left, start=1):
        current = [i]
        for j, right_char in enumerate(right, start=1):
            cost = 0 if left_char == right_char else 1
            current.append(min(current[-1] + 1, previous[j] + 1, previous[j - 1] + cost))
        previous = current
    return previous[-1]


def _expand_vagy_pair_suffix(left: str, right: str) -> list[str] | None:
    left_clean = _clean_tail_fragment(left)
    right_clean = _clean_tail_fragment(right)
    if not _is_single_word(left_clean) or not _is_single_word(right_clean):
        return None

    left_folded = _ascii_fold(left_clean.casefold())
    right_folded = _ascii_fold(right_clean.casefold())
    for suffix in PLANT_SUFFIXES:
        if right_folded.endswith(suffix) and not left_folded.endswith(suffix):
            right_stem = right_folded.removesuffix(suffix)
            if right_stem and _levenshtein_distance(left_folded, right_stem) <= LEVENSHTEIN_MAX_DISTANCE:
                return [left_clean + right_clean[-len(suffix) :], right_clean]
        if left_folded.endswith(suffix) and not right_folded.endswith(suffix):
            left_stem = left_folded.removesuffix(suffix)
            if left_stem and _levenshtein_distance(right_folded, left_stem) <= LEVENSHTEIN_MAX_DISTANCE:
                return [left_clean, right_clean + left_clean[-len(suffix) :]]
    return None


def _is_acceptable_vernacular(value: str) -> bool:
    folded_tokens = re.findall(r"[^\W\d_]+", _ascii_fold(value.casefold()), flags=re.UNICODE)
    return (
        bool(value)
        and (re.search(r"[^\W\d_]", value, flags=re.UNICODE) is not None)
        and (not _is_latin_like(value))
        and not any(token in NON_ORGANISM_SUFFIXES for token in folded_tokens)
        and value.casefold() not in NON_NAME_TAIL_TOKENS
    )


def _is_non_organism_latin_phrase(value: str) -> bool:
    tokens = _tokenize_latin_candidate(value)
    if len(tokens) < MIN_LATIN_PARTS:
        return False
    if re.fullmatch(r"[A-Z][a-z-]+", tokens[0]) is None:
        return False
    last_ascii = _ascii_fold(tokens[-1].casefold())
    return last_ascii in NON_ORGANISM_SUFFIXES


def _filter_vernacular_values(latin: str, values: set[str]) -> set[str]:
    latin_folded = latin.casefold()
    filtered: set[str] = set()
    for value in values:
        if _is_non_organism_latin_phrase(value):
            continue
        normalized = _normalize_latin_candidate(value)
        if normalized is not None and normalized.casefold() == latin_folded:
            continue
        filtered.add(value)
    return filtered


def _append_link_matches(
    line: str,
    regex: re.Pattern[str],
    matches: list[tuple[int, int, str]],
) -> None:
    for match in regex.finditer(line):
        latin = _normalize_latin_candidate(_link_value(match.group(1), match.group(2)))
        if latin:
            matches.append((match.start(), match.end(), latin))


def _latin_parenthetical_matches(line: str) -> list[tuple[int, int, str]]:
    matches: list[tuple[int, int, str]] = []
    _append_link_matches(line, LATIN_PAREN_LINK_RE, matches)
    _append_link_matches(line, LATIN_PAREN_LINK_BROKEN_RE, matches)
    for match in LATIN_PAREN_TEXT_RE.finditer(line):
        latin = _normalize_latin_candidate(match.group(1))
        if latin:
            matches.append((match.start(), match.end(), latin))
    for match in GENERIC_PAREN_RE.finditer(line):
        latin = _normalize_latin_candidate(match.group(1))
        if latin:
            matches.append((match.start(), match.end(), latin))
    matches.sort(key=operator.itemgetter(0))
    out: list[tuple[int, int, str]] = []
    seen: set[tuple[int, int, str]] = set()
    for item in matches:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _add_pairs_from_latin_parenthetical_matches(
    line: str,
    *,
    tail_plain_names: list[str],
    tail_link_names: list[str],
    mapping: dict[str, set[str]],
) -> bool:
    latin_matches = _latin_parenthetical_matches(line)
    if not latin_matches:
        return False

    previous_end = 0
    previous_names: list[str] = []
    for start, end, latin in latin_matches:
        segment = line[previous_end:start]
        segment_names = _names_from_links(segment, letter_links_only=False, exclude_latin_like=False)
        if segment_names:
            previous_names = segment_names

        if not _is_latin_like(latin):
            previous_end = end
            continue

        values: set[str] = set(tail_link_names)
        values.update(segment_names or previous_names)
        if tail_plain_names:
            values.update(tail_plain_names)
            if segment_names:
                values.add(segment_names[0])
        values = _filter_vernacular_values(latin, values)
        if values:
            mapping.setdefault(latin, set()).update(values)

        previous_end = end
    return True


def _add_pair_from_fallback(
    line: str,
    *,
    head: str,
    tail_plain_names: list[str],
    tail_link_names: list[str],
    mapping: dict[str, set[str]],
) -> None:
    latin_values = _latin_candidates_in_line(line)
    if not latin_values:
        return

    head_names = _names_from_links(head, letter_links_only=False, exclude_latin_like=False)
    values: set[str] = set(tail_link_names)
    values.update(tail_plain_names)
    if tail_plain_names and head_names:
        values.add(head_names[0])
    if (not values) and head_names:
        values.update(head_names)
    if values:
        for latin in latin_values:
            if _is_latin_like(latin):
                filtered_values = _filter_vernacular_values(latin, values)
                if filtered_values:
                    mapping.setdefault(latin, set()).update(filtered_values)


def _extract_pairs(lines: list[str]) -> dict[str, set[str]]:
    mapping: dict[str, set[str]] = {}

    for raw_line in lines:
        line = raw_line.strip()
        if not line.startswith("*"):
            continue

        parts = DASH_SPLIT_RE.split(line, maxsplit=1)
        head = parts[0]
        tail = parts[1] if len(parts) >= TAIL_SPLIT_PARTS_MIN else ""
        tail_plain_names = _names_from_tail(tail)
        tail_link_names = _names_from_links(tail, letter_links_only=True, exclude_latin_like=False)

        _add_pairs_from_latin_parenthetical_matches(
            line,
            tail_plain_names=tail_plain_names,
            tail_link_names=tail_link_names,
            mapping=mapping,
        )

        _add_pair_from_fallback(
            line,
            head=head,
            tail_plain_names=tail_plain_names,
            tail_link_names=tail_link_names,
            mapping=mapping,
        )

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
