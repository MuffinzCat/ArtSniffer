"""SQLite implementation of the storage-neutral artwork analysis cache."""

import json
import sqlite3
from pathlib import Path

from artsniffer.analysis.artwork import ArtworkAnalysis


class SQLiteAnalysisCache:
    """Persist artwork analysis using explicit JSON fields and an exact composite key."""

    def __init__(self, database_path: str | Path) -> None:
        """Open the database and create the cache schema if it does not yet exist."""
        self._connection = sqlite3.connect(database_path)
        with self._connection:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS artwork_analysis_cache (
                    artwork_id TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    model_id TEXT NOT NULL,
                    embedding_json TEXT NOT NULL,
                    tags_json TEXT NOT NULL,
                    PRIMARY KEY (artwork_id, content_hash, model_id)
                )
                """
            )

    def get(self, artwork_id: str, content_hash: str, model_id: str) -> ArtworkAnalysis | None:
        """Return analysis only for an exact artwork, content, and model version match."""
        if not isinstance(artwork_id, str) or not artwork_id.strip():
            raise ValueError("Artwork ID must not be empty or whitespace.")
        if not isinstance(content_hash, str) or not content_hash.strip():
            raise ValueError("Content hash must not be empty or whitespace.")
        if not isinstance(model_id, str) or not model_id.strip():
            raise ValueError("Model ID must not be empty or whitespace.")

        row = self._connection.execute(
            """
            SELECT embedding_json, tags_json
            FROM artwork_analysis_cache
            WHERE artwork_id = ? AND content_hash = ? AND model_id = ?
            """,
            (artwork_id, content_hash, model_id),
        ).fetchone()
        if row is None:
            return None

        embedding_values = json.loads(row[0])
        tags = json.loads(row[1])
        if not isinstance(embedding_values, list) or any(
            isinstance(value, bool) or not isinstance(value, (int, float))
            for value in embedding_values
        ):
            raise ValueError("Stored analysis embedding must be a JSON number array.")
        if not isinstance(tags, list) or any(not isinstance(tag, str) for tag in tags):
            raise ValueError("Stored analysis tags must be a JSON string array.")

        return ArtworkAnalysis(
            artwork_id=artwork_id,
            model_id=model_id,
            embedding=tuple(float(value) for value in embedding_values),
            tags=tuple(tags),
        )

    def put(self, analysis: ArtworkAnalysis, content_hash: str) -> None:
        """Insert or replace a cached result without storing source artwork bytes."""
        if not isinstance(content_hash, str) or not content_hash.strip():
            raise ValueError("Content hash must not be empty or whitespace.")

        embedding_json = json.dumps(analysis.embedding, separators=(",", ":"), allow_nan=False)
        tags_json = json.dumps(analysis.tags, separators=(",", ":"), ensure_ascii=False)
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO artwork_analysis_cache (
                    artwork_id, content_hash, model_id, embedding_json, tags_json
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (artwork_id, content_hash, model_id) DO UPDATE SET
                    embedding_json = excluded.embedding_json,
                    tags_json = excluded.tags_json
                """,
                (
                    analysis.artwork_id,
                    content_hash,
                    analysis.model_id,
                    embedding_json,
                    tags_json,
                ),
            )

    def close(self) -> None:
        """Close the database connection."""
        self._connection.close()
