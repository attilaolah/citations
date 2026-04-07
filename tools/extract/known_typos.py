"""Shared typo normalization for source extractors."""

KNOWN_HUNGARIAN_TYPOS = {
    # Copy-paste artifact from:
    # https://www.gyakorikerdesek.hu/otthon__kert__168054-a-pitypangnak-hany-fele-elnevezese-van-
    "de barátfej": "barátfej",
    "kákicsn": "kákics",
    # Missing or wrong accents:
    "sarga liliom": "sárga liliom",
}


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
