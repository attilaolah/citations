"""Shared extract models and adapters."""

from pydantic import BaseModel, TypeAdapter


class VernacularName(BaseModel):
    """Vernacular entry from extractor or clean output."""

    verbatim: str
    canonical: str | None = None


class CleanEntry(BaseModel):
    """Subset of cleaned entry data used by tests."""

    normalized: str
    vernacular: dict[str, list[VernacularName]] | None = None


PAIRS_ADAPTER = TypeAdapter(dict[str, list[str | VernacularName]])
CLEAN_ENTRIES_ADAPTER = TypeAdapter(list[CleanEntry])
