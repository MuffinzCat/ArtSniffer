"""SQLite persistence for minimal e621/e926 discovery watermarks."""

import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class E621DiscoveryState:
    """Preserve the last successful position for one configured provider source."""

    source_id: str
    host: str
    tag_search_expression: str
    high_watermark: int | None = None
    catch_up_incomplete: bool = False

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError("e621/e926 source ID must not be empty or whitespace.")
        if self.host not in ("e621.net", "e926.net"):
            raise ValueError("e621/e926 host must be 'e621.net' or 'e926.net'.")
        if not self.tag_search_expression.strip():
            raise ValueError("e621/e926 tag search expression must not be empty or whitespace.")
        if self.high_watermark is not None:
            if isinstance(self.high_watermark, bool) or not isinstance(self.high_watermark, int):
                raise ValueError("e621/e926 high watermark must be an integer or null.")
        if not isinstance(self.catch_up_incomplete, bool):
            raise ValueError("e621/e926 catch-up incomplete flag must be a boolean.")


class SQLiteE621DiscoveryStateStore:
    """Persist one e621/e926 watermark per source, host, and exact tag expression."""

    def __init__(self, database_path: str | Path) -> None:
        self._connection = sqlite3.connect(database_path)
        with self._connection:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS e621_discovery_state (
                    source_id TEXT NOT NULL,
                    host TEXT NOT NULL,
                    tag_search_expression TEXT NOT NULL,
                    high_watermark INTEGER,
                    catch_up_incomplete INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (source_id, host, tag_search_expression)
                )
                """
            )

    def get(
        self,
        source_id: str,
        host: str,
        tag_search_expression: str,
    ) -> E621DiscoveryState:
        if not source_id.strip():
            raise ValueError("e621/e926 source ID must not be empty or whitespace.")
        if host not in ("e621.net", "e926.net"):
            raise ValueError("e621/e926 host must be 'e621.net' or 'e926.net'.")
        if not tag_search_expression.strip():
            raise ValueError("e621/e926 tag search expression must not be empty or whitespace.")
        row = self._connection.execute(
            """
            SELECT high_watermark, catch_up_incomplete, typeof(catch_up_incomplete)
            FROM e621_discovery_state
            WHERE source_id = ? AND host = ? AND tag_search_expression = ?
            """,
            (source_id, host, tag_search_expression),
        ).fetchone()
        if row is None:
            return E621DiscoveryState(
                source_id=source_id,
                host=host,
                tag_search_expression=tag_search_expression,
            )
        catch_up_incomplete = row[1]
        catch_up_incomplete_type = row[2]
        if (
            catch_up_incomplete_type != "integer"
            or isinstance(catch_up_incomplete, bool)
            or not isinstance(catch_up_incomplete, int)
            or catch_up_incomplete not in (0, 1)
        ):
            raise ValueError(
                "Persisted e621/e926 catch-up incomplete value must be SQLite integer 0 or 1."
            )
        return E621DiscoveryState(
            source_id=source_id,
            host=host,
            tag_search_expression=tag_search_expression,
            high_watermark=row[0],
            catch_up_incomplete=catch_up_incomplete == 1,
        )

    def save(self, state: E621DiscoveryState) -> None:
        if not isinstance(state, E621DiscoveryState):
            raise ValueError("State must be an E621DiscoveryState.")
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO e621_discovery_state (
                    source_id,
                    host,
                    tag_search_expression,
                    high_watermark,
                    catch_up_incomplete
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (source_id, host, tag_search_expression) DO UPDATE SET
                    high_watermark = excluded.high_watermark,
                    catch_up_incomplete = excluded.catch_up_incomplete
                """,
                (
                    state.source_id,
                    state.host,
                    state.tag_search_expression,
                    state.high_watermark,
                    int(state.catch_up_incomplete),
                ),
            )

    def save_many(self, states: tuple[E621DiscoveryState, ...]) -> None:
        """Atomically replace or insert a complete scan's expression states."""
        if any(not isinstance(state, E621DiscoveryState) for state in states):
            raise ValueError("State values must be E621DiscoveryState values.")
        with self._connection:
            for state in states:
                self._connection.execute(
                    """
                    INSERT INTO e621_discovery_state (
                        source_id,
                        host,
                        tag_search_expression,
                        high_watermark,
                        catch_up_incomplete
                    )
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT (source_id, host, tag_search_expression) DO UPDATE SET
                        high_watermark = excluded.high_watermark,
                        catch_up_incomplete = excluded.catch_up_incomplete
                    """,
                    (
                        state.source_id,
                        state.host,
                        state.tag_search_expression,
                        state.high_watermark,
                        int(state.catch_up_incomplete),
                    ),
                )

    def close(self) -> None:
        self._connection.close()
