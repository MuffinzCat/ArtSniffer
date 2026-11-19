"""Tests for the SQLite-backed reference artwork store."""

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest

from artsniffer.persistence.reference_artwork import ReferenceArtworkStore
from artsniffer.persistence.sqlite_reference_artwork import SQLiteReferenceArtworkStore
from artsniffer.references.artwork import ArtworkRecord


@pytest.fixture
def sqlite_store(tmp_path: Path) -> Iterator[SQLiteReferenceArtworkStore]:
    store = SQLiteReferenceArtworkStore(tmp_path / "reference.sqlite")
    try:
        yield store
    finally:
        store.close()


def artwork(
    artwork_id: str,
    source_id: str,
    source_item_id: str,
    content_hash: str = "sha256:v1",
) -> ArtworkRecord:
    return ArtworkRecord(artwork_id, source_id, source_item_id, content_hash)


def test_sqlite_store_round_trips_source_state(sqlite_store: ReferenceArtworkStore) -> None:
    artworks = (
        artwork("art-a", "source-a", "item-a"),
        artwork("art-b", "source-a", "item-b", "sha256:v2"),
    )

    sqlite_store.replace_for_source("source-a", artworks)

    assert sqlite_store.get_for_source("source-a") == artworks
    assert sqlite_store.get_for_source("source-b") == ()


def test_sqlite_store_survives_reopening_database(tmp_path: Path) -> None:
    database_path = tmp_path / "reference.sqlite"
    expected = (artwork("art-a", "source-a", "item-a"),)
    store = SQLiteReferenceArtworkStore(database_path)
    store.replace_for_source("source-a", expected)
    store.close()

    reopened = SQLiteReferenceArtworkStore(database_path)
    try:
        assert reopened.get_for_source("source-a") == expected
    finally:
        reopened.close()


def test_complete_replacement_is_source_isolated(
    sqlite_store: ReferenceArtworkStore,
) -> None:
    source_a_old = (
        artwork("art-a1", "source-a", "item-a1"),
        artwork("art-a2", "source-a", "item-a2"),
    )
    source_b = (artwork("art-b", "source-b", "item-b"),)
    sqlite_store.replace_for_source("source-a", source_a_old)
    sqlite_store.replace_for_source("source-b", source_b)

    source_a_new = (artwork("art-a3", "source-a", "item-a3", "sha256:v3"),)
    sqlite_store.replace_for_source("source-a", source_a_new)

    assert sqlite_store.get_for_source("source-a") == source_a_new
    assert sqlite_store.get_for_source("source-b") == source_b


def test_empty_replacement_removes_only_that_source(
    sqlite_store: ReferenceArtworkStore,
) -> None:
    sqlite_store.replace_for_source(
        "source-a",
        (artwork("art-a", "source-a", "item-a"),),
    )
    source_b = (artwork("art-b", "source-b", "item-b"),)
    sqlite_store.replace_for_source("source-b", source_b)

    sqlite_store.replace_for_source("source-a", ())

    assert sqlite_store.get_for_source("source-a") == ()
    assert sqlite_store.get_for_source("source-b") == source_b


@pytest.mark.parametrize("source_id", ["", " \t\n"])
def test_store_rejects_blank_source(
    sqlite_store: ReferenceArtworkStore,
    source_id: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=r"\ASource ID must not be empty or whitespace\.\Z",
    ):
        sqlite_store.get_for_source(source_id)
    with pytest.raises(
        ValueError,
        match=r"\ASource ID must not be empty or whitespace\.\Z",
    ):
        sqlite_store.replace_for_source(source_id, ())


def test_store_rejects_wrong_source_in_replacement(
    sqlite_store: ReferenceArtworkStore,
) -> None:
    with pytest.raises(
        ValueError, match=r"\AArtwork source ID must match replacement source ID\.\Z"
    ):
        sqlite_store.replace_for_source(
            "source-a",
            (artwork("art-b", "source-b", "item-b"),),
        )
    assert sqlite_store.get_for_source("source-a") == ()


def test_store_rejects_duplicate_source_item_in_replacement(
    sqlite_store: ReferenceArtworkStore,
) -> None:
    with pytest.raises(
        ValueError,
        match=r"\ADuplicate source item ID in replacement: item-a\.\Z",
    ):
        sqlite_store.replace_for_source(
            "source-a",
            (
                artwork("art-a1", "source-a", "item-a"),
                artwork("art-a2", "source-a", "item-a"),
            ),
        )


def test_store_rejects_duplicate_artwork_id_in_replacement(
    sqlite_store: ReferenceArtworkStore,
) -> None:
    with pytest.raises(
        ValueError,
        match=r"\ADuplicate artwork ID in replacement: art-a\.\Z",
    ):
        sqlite_store.replace_for_source(
            "source-a",
            (
                artwork("art-a", "source-a", "item-a1"),
                artwork("art-a", "source-a", "item-a2"),
            ),
        )


def test_store_rejects_duplicate_artwork_id_across_sources_atomically(
    sqlite_store: ReferenceArtworkStore,
) -> None:
    sqlite_store.replace_for_source(
        "source-a",
        (artwork("art-shared", "source-a", "item-a"),),
    )

    with pytest.raises(sqlite3.IntegrityError):
        sqlite_store.replace_for_source(
            "source-b",
            (artwork("art-shared", "source-b", "item-b"),),
        )

    assert sqlite_store.get_for_source("source-a") == (artwork("art-shared", "source-a", "item-a"),)
    assert sqlite_store.get_for_source("source-b") == ()


def test_failed_insert_rolls_back_complete_replacement(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "reference.sqlite"
    store = SQLiteReferenceArtworkStore(database_path)
    try:
        original = (artwork("art-old", "source-a", "item-old"),)
        store.replace_for_source("source-a", original)
        with sqlite3.connect(database_path) as connection:
            connection.execute(
                """
                CREATE TRIGGER fail_reference_artwork_insert
                BEFORE INSERT ON reference_artwork_state
                BEGIN
                    SELECT RAISE(ABORT, 'forced reference artwork insert failure');
                END
                """
            )

        with pytest.raises(sqlite3.IntegrityError, match="forced reference artwork insert failure"):
            store.replace_for_source(
                "source-a",
                (artwork("art-new", "source-a", "item-new"),),
            )

        assert store.get_for_source("source-a") == original
    finally:
        store.close()
