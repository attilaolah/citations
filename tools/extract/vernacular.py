"""Shared helpers for vernacular output shaping."""

from tools.extract.known_typos import normalize_hungarian_canonical


def sorted_vernacular_entries(values: set[str]) -> list[dict[str, str]]:
    """Return deterministic vernacular output objects for cleaned values.

    Returns:
        List of `{canonical, verbatim}` objects sorted by canonical then verbatim.
    """
    unique: dict[tuple[str, str], dict[str, str]] = {}
    for verbatim in values:
        canonical = normalize_hungarian_canonical(verbatim)
        unique[canonical, verbatim] = {
            "canonical": canonical,
            "verbatim": verbatim,
        }
    return [unique[key] for key in sorted(unique, key=lambda item: (item[0], item[1].casefold()))]
