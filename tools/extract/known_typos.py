"""Shared Hungarian vernacular normalization utilities."""

import re
import unicodedata

KNOWN_HUNGARIAN_TYPOS = {
    # Copy-paste artifact from:
    # https://www.gyakorikerdesek.hu/otthon__kert__168054-a-pitypangnak-hany-fele-elnevezese-van-
    "de barátfej": "barátfej",
    "kákicsn": "kákics",
    # Missing or wrong accents:
    "sarga liliom": "sárga liliom",
}

KNOWN_PROPER_NOUN_HYPHEN_PREFIXES = {
    "hayward",
    "kovacs",
    "pallas",
    "steller",
    "tallos",
}
KNOWN_COMPOUND_JOINS = {
    "fenyő": {
        "lúcz",
        "puha",
        "sima",
    },
}
KNOWN_COMPOUND_PARTS = 2

SAINT_PREFIX_RE = re.compile(r"^(?:szt\.?|szent)[\s\-.]*", flags=re.IGNORECASE)
NON_WORD_SEPARATOR_RE = re.compile(r"[\s-]+")
VENUS_WORD_RE = re.compile(r"(?<!\w)venus(?!\w)")


def normalize_known_hungarian_typo(value: str) -> str:
    """Normalize a value using the repository-wide known typo mapping.

    Returns:
        Corrected value when a known typo exists, otherwise normalized input.
    """
    normalized = " ".join(value.split())
    replacement = KNOWN_HUNGARIAN_TYPOS.get(normalized.casefold())
    if replacement is None:
        return normalized

    if normalized[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def _strip_diacritics(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def normalize_hungarian_canonical(value: str) -> str:
    """Return canonical Hungarian vernacular with typo and case normalization.

    Returns:
        Canonicalized value intended for deterministic comparisons.
    """
    normalized = normalize_known_hungarian_typo(value)
    normalized = _normalize_saint_prefix(normalized)
    canonical = normalized.casefold()
    canonical = _join_known_compounds(canonical)
    canonical = _restore_hyphenated_proper_prefix(canonical)
    return VENUS_WORD_RE.sub("Venus", canonical)


def normalize_hungarian_light_canonical(value: str) -> str:
    """Return lightweight canonical Hungarian vernacular normalization.

    Returns:
        Lower-cased, whitespace-normalized value with Venus proper-noun fix.
    """
    canonical = " ".join(value.split()).casefold()
    return VENUS_WORD_RE.sub("Venus", canonical)


def _normalize_saint_prefix(value: str) -> str:
    match = SAINT_PREFIX_RE.match(value.strip())
    if match is None:
        return " ".join(value.split())

    remainder = value[match.end() :].strip()
    remainder = NON_WORD_SEPARATOR_RE.sub("", remainder)
    if not remainder:
        return "szent"
    return "szent" + remainder


def _restore_hyphenated_proper_prefix(value: str) -> str:
    if "-" not in value:
        return value

    prefix, remainder = value.split("-", 1)
    if prefix.endswith(("i", "ii")):
        return value
    if _strip_diacritics(prefix) not in KNOWN_PROPER_NOUN_HYPHEN_PREFIXES:
        return value
    return prefix[:1].upper() + prefix[1:] + "-" + remainder


def _join_known_compounds(value: str) -> str:
    parts = value.split()
    if len(parts) != KNOWN_COMPOUND_PARTS:
        return value

    prefix, head = parts
    join_prefixes = KNOWN_COMPOUND_JOINS.get(head)
    if join_prefixes is None:
        return value
    if prefix not in join_prefixes:
        return value
    return prefix + head
