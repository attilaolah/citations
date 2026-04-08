"""Lookup helpers for CoL scientific names stored in DuckDB."""

from dataclasses import dataclass
from re import escape
from typing import TYPE_CHECKING

from Levenshtein import distance as levenshtein_distance
from sqlalchemy import String, create_engine, func, or_, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine
    from sqlalchemy.sql.elements import ColumnElement

_GENDER_SUFFIXES = ("a", "us", "um")
_BINOMIAL_TOKEN_COUNT = 2


class Base(DeclarativeBase):
    """Base class for SQLAlchemy ORM models."""


class ColNameUsage(Base):
    """Minimal ORM model used by lookup logic."""

    __tablename__ = "col_name_usage"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    scientific_name: Mapped[str] = mapped_column(String)
    canonical_scientific_name: Mapped[str] = mapped_column(String)


@dataclass(frozen=True, slots=True)
class LookupResult:
    """Lookup result returned by the resolver."""

    id: str
    scientific_name: str
    canonical_scientific_name: str


def _token_gender_variants(token: str) -> tuple[str, ...]:
    lowered = token.casefold()
    for suffix in _GENDER_SUFFIXES:
        if lowered.endswith(suffix):
            stem = token[: len(token) - len(suffix)]
            return tuple(f"{stem}{candidate}" for candidate in _GENDER_SUFFIXES)
    return (token,)


def _binomial_subgenus_pattern(name: str) -> str | None:
    tokens = name.split()
    if len(tokens) != _BINOMIAL_TOKEN_COUNT:
        return None
    return f"{tokens[0]} (%) {tokens[1]}"


def _genus_two_words_stem_pattern(name: str) -> str:
    tokens = name.split()
    if len(tokens) < _BINOMIAL_TOKEN_COUNT:
        return name
    last = tokens[-1]
    for suffix in _GENDER_SUFFIXES:
        if last.casefold().endswith(suffix):
            stem = last[: len(last) - len(suffix)]
            return f"{tokens[0]} % % {stem}%"
    return f"{tokens[0]} % % {last}%"


def _to_result(row: ColNameUsage | None) -> LookupResult | None:
    if row is None:
        return None
    return LookupResult(
        id=row.id,
        scientific_name=row.scientific_name,
        canonical_scientific_name=row.canonical_scientific_name,
    )


def _first_match(session: Session, scientific_name: str) -> LookupResult | None:
    statement = select(ColNameUsage).where(ColNameUsage.scientific_name == scientific_name).limit(1)
    return _to_result(session.execute(statement).scalar_one_or_none())


def _lookup_subgenus(session: Session, query: str) -> LookupResult | None:
    pattern = _binomial_subgenus_pattern(query)
    if pattern is None:
        return None
    return _to_result(
        session.execute(
            select(ColNameUsage).where(ColNameUsage.scientific_name.like(pattern)).limit(1),
        ).scalar_one_or_none(),
    )


def _lookup_gender_variants(session: Session, query: str) -> LookupResult | None:
    tokens = query.split()
    if len(tokens) < _BINOMIAL_TOKEN_COUNT:
        return None
    first_variants = _token_gender_variants(tokens[0])
    last_variants = _token_gender_variants(tokens[-1])
    for first in first_variants:
        for last in last_variants:
            if first == tokens[0] and last == tokens[-1]:
                continue
            candidate = " ".join([first, *tokens[1:-1], last])
            variant_match = _first_match(session, candidate)
            if variant_match is not None:
                return variant_match
    return None


def _lookup_genus_stem_pattern(session: Session, query: str) -> LookupResult | None:
    pattern = _genus_two_words_stem_pattern(query)
    return _to_result(
        session.execute(
            select(ColNameUsage).where(ColNameUsage.scientific_name.like(pattern)).limit(1),
        ).scalar_one_or_none(),
    )


def _word_match_clause(words: list[str]) -> ColumnElement[bool]:
    clauses: list[ColumnElement[bool]] = []
    for word in words:
        escaped_word = escape(word)
        clauses.append(func.regexp_matches(ColNameUsage.scientific_name, rf"(^| ){escaped_word}( |$)"))
    clause = clauses[0]
    for extra in clauses[1:]:
        clause = or_(clause, extra)
    return clause


def _lookup_by_levenshtein(session: Session, query: str) -> LookupResult | None:
    words = [word for word in query.split() if word]
    statement = select(ColNameUsage).where(_word_match_clause(words))
    rows = list(session.execute(statement).scalars())
    if not rows:
        return None
    best = min(rows, key=lambda row: (levenshtein_distance(row.scientific_name, query), row.scientific_name))
    return _to_result(best)


def lookup_name(session: Session, query: str) -> LookupResult | None:
    """Resolve a scientific name using increasingly permissive strategies.

    Args:
        session: Active SQLAlchemy session on a DuckDB database.
        query: Scientific name query to resolve.

    Returns:
        Matching record, or `None` if no strategy finds a result.
    """
    normalized_query = " ".join(query.split())
    if not normalized_query:
        return None
    for strategy in (
        _first_match,
        _lookup_subgenus,
        _lookup_gender_variants,
        _lookup_genus_stem_pattern,
        _lookup_by_levenshtein,
    ):
        result = strategy(session, normalized_query)
        if result is not None:
            return result
    return None


def create_duckdb_engine(db_path: str, *, read_only: bool = True) -> Engine:
    """Create a DuckDB SQLAlchemy engine for a local database file.

    Args:
        db_path: Path to the DuckDB file.
        read_only: Whether to open the database read-only.

    Returns:
        Configured SQLAlchemy engine.
    """
    return create_engine(f"duckdb:///{db_path}", connect_args={"read_only": read_only})
