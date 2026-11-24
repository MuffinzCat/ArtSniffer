"""Synthetic tests for persisted e621/e926 discovery watermarks."""

import sqlite3
from pathlib import Path

import pytest

from artsniffer.persistence.e621_discovery_state import (
    E621DiscoveryState,
    SQLiteE621DiscoveryStateStore,
)


def test_state_round_trips_source_watermark(tmp_path: Path) -> None:
    store = SQLiteE621DiscoveryStateStore(tmp_path / "e621.sqlite")
    try:
        store.save(
            E621DiscoveryState(
                source_id="art",
                host="e621.net",
                tag_search_expression="fox",
                high_watermark=6880578,
                catch_up_incomplete=True,
            )
        )

        assert store.get("art", "e621.net", "fox") == E621DiscoveryState(
            source_id="art",
            host="e621.net",
            tag_search_expression="fox",
            high_watermark=6880578,
            catch_up_incomplete=True,
        )
    finally:
        store.close()


def test_state_survives_reopening(tmp_path: Path) -> None:
    database_path = tmp_path / "e621.sqlite"
    store = SQLiteE621DiscoveryStateStore(database_path)
    store.save(
        E621DiscoveryState(
            source_id="art",
            host="e926.net",
            tag_search_expression="cat",
            high_watermark=123,
        )
    )
    store.close()

    reopened = SQLiteE621DiscoveryStateStore(database_path)
    try:
        assert reopened.get("art", "e926.net", "cat").high_watermark == 123
        assert reopened.get("art", "e621.net", "fox").high_watermark is None
    finally:
        reopened.close()


def test_states_are_isolated_by_source_and_host(tmp_path: Path) -> None:
    store = SQLiteE621DiscoveryStateStore(tmp_path / "e621.sqlite")
    try:
        store.save(E621DiscoveryState("first", "e621.net", "fox", 100))
        store.save(E621DiscoveryState("second", "e621.net", "fox", 200))
        store.save(E621DiscoveryState("first", "e926.net", "fox", 300))
        store.save(E621DiscoveryState("first", "e621.net", "cat", 400))

        assert store.get("first", "e621.net", "fox").high_watermark == 100
        assert store.get("second", "e621.net", "fox").high_watermark == 200
        assert store.get("first", "e926.net", "fox").high_watermark == 300
        assert store.get("first", "e621.net", "cat").high_watermark == 400
    finally:
        store.close()


@pytest.mark.parametrize("source_id", ["", " \t"])
def test_state_rejects_blank_source_id(tmp_path: Path, source_id: str) -> None:
    with pytest.raises(ValueError, match="source ID"):
        E621DiscoveryState(source_id, "e621.net", "fox", 100)


@pytest.mark.parametrize("host", ["", "example.com"])
def test_state_rejects_invalid_host(tmp_path: Path, host: str) -> None:
    with pytest.raises(ValueError, match="host"):
        E621DiscoveryState("art", host, "fox", 100)


@pytest.mark.parametrize("expression", ["", " \t"])
def test_state_rejects_blank_expression(tmp_path: Path, expression: str) -> None:
    with pytest.raises(ValueError, match="tag search expression"):
        E621DiscoveryState("art", "e621.net", expression, 100)


@pytest.mark.parametrize("persisted_value", [-1, 2, sqlite3.Binary(b"1")])
def test_persisted_catch_up_incomplete_must_be_exact_integer(
    tmp_path: Path,
    persisted_value: object,
) -> None:
    database_path = tmp_path / "e621.sqlite"
    store = SQLiteE621DiscoveryStateStore(database_path)
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            INSERT INTO e621_discovery_state (
                source_id,
                host,
                tag_search_expression,
                high_watermark,
                catch_up_incomplete
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            ("art", "e621.net", "fox", 100, persisted_value),
        )

    try:
        with pytest.raises(
            ValueError,
            match="catch-up incomplete value must be SQLite integer 0 or 1",
        ):
            store.get("art", "e621.net", "fox")
    finally:
        store.close()
