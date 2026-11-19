"""SQLite implementation of persistent reference artwork state."""

import sqlite3
from collections.abc import Sequence
from pathlib import Path

from artsniffer.references.artwork import ArtworkRecord


class SQLiteReferenceArtworkStore:
    """Store one complete reference artwork state per source."""

    def __init__(self, database_path: str | Path) -> None:
        """Open the database and create the reference artwork schema if needed."""
        self._connection = sqlite3.connect(database_path)
        with self._connection:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS reference_artwork_state (
                    artwork_id TEXT NOT NULL UNIQUE,
                    source_id TEXT NOT NULL,
                    source_item_id TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    PRIMARY KEY (source_id, source_item_id)
                )
                """
            )

    def get_for_source(self, source_id: str) -> Sequence[ArtworkRecord]:
        """Retrieve the current artwork records for one source."""
        if not isinstance(source_id, str) or not source_id.strip():
            raise ValueError("Source ID must not be empty or whitespace.")

        rows = self._connection.execute(
            """
            SELECT artwork_id, source_id, source_item_id, content_hash
            FROM reference_artwork_state
            WHERE source_id = ?
            ORDER BY source_item_id
            """,
            (source_id,),
        ).fetchall()
        return tuple(
            ArtworkRecord(
                id=row[0],
                source_id=row[1],
                source_item_id=row[2],
                content_hash=row[3],
            )
            for row in rows
        )

    def replace_for_source(
        self,
        source_id: str,
        artworks: Sequence[ArtworkRecord],
    ) -> None:
        """Atomically replace one source's complete current artwork state."""
        if not isinstance(source_id, str) or not source_id.strip():
            raise ValueError("Source ID must not be empty or whitespace.")

        seen_item_ids: set[str] = set()
        seen_artwork_ids: set[str] = set()
        validated: list[tuple[str, str, str, str]] = []
        for artwork in artworks:
            if not isinstance(artwork, ArtworkRecord):
                raise ValueError("Reference artwork state must contain ArtworkRecord values.")
            if artwork.source_id != source_id:
                raise ValueError("Artwork source ID must match replacement source ID.")
            if artwork.source_item_id in seen_item_ids:
                raise ValueError(
                    f"Duplicate source item ID in replacement: {artwork.source_item_id}."
                )
            if artwork.id in seen_artwork_ids:
                raise ValueError(f"Duplicate artwork ID in replacement: {artwork.id}.")
            seen_item_ids.add(artwork.source_item_id)
            seen_artwork_ids.add(artwork.id)
            validated.append(
                (artwork.id, artwork.source_id, artwork.source_item_id, artwork.content_hash)
            )

        with self._connection:
            self._connection.execute(
                "DELETE FROM reference_artwork_state WHERE source_id = ?",
                (source_id,),
            )
            self._connection.executemany(
                """
                INSERT INTO reference_artwork_state (
                    artwork_id, source_id, source_item_id, content_hash
                )
                VALUES (?, ?, ?, ?)
                """,
                validated,
            )

    def close(self) -> None:
        """Close the database connection."""
        self._connection.close()
