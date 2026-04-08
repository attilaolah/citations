"""Tests for CoL lookup strategy fallbacks."""

import sys
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from tools.col.lookup import Base, ColNameUsage, lookup_name

if TYPE_CHECKING:
    from collections.abc import Generator


def _insert_name(session: Session, identifier: str, scientific_name: str, canonical_name: str) -> None:
    session.add(
        ColNameUsage(
            id=identifier,
            scientific_name=scientific_name,
            canonical_scientific_name=canonical_name,
        ),
    )


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
        ("Carabus hungaricus", "subgen-1"),
        ("Mentha piperita", "last-1"),
        ("Fungus alba", "first-last-1"),
        ("Achillea asplenifolia", "stem-1"),
        ("Actea spicata", "lev-1"),
        ("Nope neverfoundii", None),
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


if __name__ == "__main__":
    raise SystemExit(pytest.main(sys.argv[1:]))
