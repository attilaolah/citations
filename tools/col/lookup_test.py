"""Tests for CoL lookup strategy fallbacks."""

from typing import TYPE_CHECKING

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from tools.col.lookup import Base, ColNameUsage, create_duckdb_engine, lookup_name

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture
def session() -> Generator[Session]:
    """Provide an in-memory DuckDB-backed SQLAlchemy session.

    Yields:
        Session populated with synthetic `col_name_usage` rows.
    """
    engine = create_engine("duckdb:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as value:
        _insert_name(value, "exact-1", "Pinus sylvestris", "Pinus sylvestris")
        _insert_name(value, "exact-2", "Esox", "Esox")
        _insert_name(value, "subgen-1", "Carabus (Pachystus) hungaricus", "Carabus (Pachystus) hungaricus")
        _insert_name(value, "last-1", "Mentha piperitum", "Mentha piperitum")
        _insert_name(value, "first-last-1", "Funga album", "Funga album")
        _insert_name(value, "stem-1", "Achillea sectio major asplenifolium", "Achillea asplenifolium")
        _insert_name(value, "lev-1", "Actaea spicata", "Actaea spicata")
        value.commit()
        yield value


@pytest.mark.parametrize(
    ("query", "expected_id"),
    [
        ("Pinus sylvestris", "exact-1"),
        ("Pinus", None),
        ("Esox", "exact-2"),
        ("Carabus hungaricus", "subgen-1"),
        ("Mentha piperita", "last-1"),
        ("Fungus alba", "first-last-1"),
        ("Achillea asplenifolia", "stem-1"),
        ("Actea spicata", "lev-1"),
        ("Nope neverfoundii", None),
        ("   ", None),
    ],
)
def test_lookup_branches(session: Session, query: str, expected_id: str | None) -> None:
    """Resolve names through exact, fallback, and typo-tolerant branches."""
    result = lookup_name(session, query)
    if expected_id is None:
        assert result is None
        return
    assert result is not None
    assert result.id == expected_id


def test_lookup_by_levenshtein_honors_default_max_distance(session: Session) -> None:
    """Reject far matches when Levenshtein distance exceeds the default threshold."""
    result = lookup_name(session, "Actaaaaaaaa spicata")
    assert result is None


def test_lookup_by_levenshtein_allows_configured_max_distance(session: Session) -> None:
    """Allow farther typo matches when configured threshold is higher."""
    result = lookup_name(session, "Actaaaaaaaa spicata", max_levenshtein_distance=8)
    assert result is not None
    assert result.id == "lev-1"


def test_lookup_manual_override() -> None:
    """Resolve hard-coded names that are known missing from current CoL snapshot."""
    engine = create_engine("duckdb:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        result = lookup_name(session, "Virola calophylloidea")
        assert result is not None
        assert result.id == "5BK4D"
        assert result.scientific_name == "Virola calophylloidea"
        assert result.canonical_scientific_name == "Virola calophylloidea"


def test_create_duckdb_engine() -> None:
    """Create an engine for a local database path."""
    db_path = "lookup-test.duckdb"
    engine = create_duckdb_engine(db_path)
    try:
        assert str(engine.url).endswith(db_path)
    finally:
        engine.dispose()


def _insert_name(session: Session, identifier: str, scientific_name: str, canonical_name: str) -> None:
    session.add(
        ColNameUsage(
            id=identifier,
            scientific_name=scientific_name,
            canonical_scientific_name=canonical_name,
        ),
    )
