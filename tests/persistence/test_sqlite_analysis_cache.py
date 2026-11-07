"""Tests for the SQLite-backed artwork analysis cache."""

from collections.abc import Iterator

import pytest

from artsniffer.analysis.artwork import ArtworkAnalysis
from artsniffer.persistence.analysis_cache import AnalysisCache
from artsniffer.persistence.sqlite_analysis_cache import SQLiteAnalysisCache


@pytest.fixture
def sqlite_cache(tmp_path) -> Iterator[SQLiteAnalysisCache]:
    cache = SQLiteAnalysisCache(tmp_path / "analysis.sqlite")
    try:
        yield cache
    finally:
        cache.close()


def _analysis(model_id: str = "visual-model-v1") -> ArtworkAnalysis:
    return ArtworkAnalysis(
        artwork_id="artwork-001",
        model_id=model_id,
        embedding=(-1.5, 0.0, 2.25),
        tags=("watercolour", "landscape"),
    )


def test_sqlite_analysis_cache_round_trips_analysis(sqlite_cache: AnalysisCache) -> None:
    analysis = _analysis()

    sqlite_cache.put(analysis, "sha256:content-v1")

    assert sqlite_cache.get("artwork-001", "sha256:content-v1", "visual-model-v1") == analysis
    assert sqlite_cache.get("artwork-002", "sha256:content-v1", "visual-model-v1") is None


@pytest.mark.parametrize(
    ("artwork_id", "content_hash", "model_id", "message"),
    [
        ("", "sha256:content-v1", "visual-model-v1", "Artwork ID"),
        (" \t\n", "sha256:content-v1", "visual-model-v1", "Artwork ID"),
        ("artwork-001", "", "visual-model-v1", "Content hash"),
        ("artwork-001", " \t\n", "visual-model-v1", "Content hash"),
        ("artwork-001", "sha256:content-v1", "", "Model ID"),
        ("artwork-001", "sha256:content-v1", " \t\n", "Model ID"),
    ],
)
def test_sqlite_analysis_cache_rejects_malformed_lookup_identity(
    sqlite_cache: AnalysisCache,
    artwork_id: str,
    content_hash: str,
    model_id: str,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=rf"\A{message} must not be empty or whitespace\.\Z"):
        sqlite_cache.get(artwork_id, content_hash, model_id)


def test_sqlite_analysis_cache_does_not_reuse_changed_content_or_model(
    sqlite_cache: AnalysisCache,
) -> None:
    sqlite_cache.put(_analysis(), "sha256:content-v1")

    assert sqlite_cache.get("artwork-001", "sha256:content-v2", "visual-model-v1") is None
    assert sqlite_cache.get("artwork-001", "sha256:content-v1", "visual-model-v2") is None


def test_sqlite_analysis_cache_survives_reopening_database(tmp_path) -> None:
    database_path = tmp_path / "analysis.sqlite"
    analysis = _analysis()
    cache = SQLiteAnalysisCache(database_path)
    cache.put(analysis, "sha256:content-v1")
    cache.close()

    reopened_cache = SQLiteAnalysisCache(database_path)

    assert reopened_cache.get("artwork-001", "sha256:content-v1", "visual-model-v1") == analysis
    reopened_cache.close()


@pytest.mark.parametrize("content_hash", ["", " ", "\t\n"])
def test_sqlite_analysis_cache_rejects_empty_content_hash(
    sqlite_cache: AnalysisCache, content_hash: str
) -> None:
    with pytest.raises(ValueError, match=r"\AContent hash must not be empty or whitespace\.\Z"):
        sqlite_cache.put(_analysis(), content_hash)
