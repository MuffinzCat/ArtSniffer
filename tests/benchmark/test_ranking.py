"""Tests for ranking benchmark analyses by embedding similarity."""

import pytest

from artsniffer.analysis.artwork import ArtworkAnalysis
from artsniffer.benchmark.analysis import BenchmarkAnalysis
from artsniffer.benchmark.ranking import rank_benchmark_matches


def _benchmark_analysis(
    artwork_id: str, model_id: str, embedding: tuple[float, ...]
) -> BenchmarkAnalysis:
    analysis = ArtworkAnalysis(
        artwork_id=artwork_id,
        model_id=model_id,
        embedding=embedding,
    )
    return BenchmarkAnalysis(
        model_id=model_id,
        artwork_id=artwork_id,
        analysis=analysis,
        elapsed_seconds=0.0,
    )


def test_rank_benchmark_matches_orders_candidates_by_similarity() -> None:
    query = _benchmark_analysis("query", "model-1", (1.0, 0.0))
    candidates = (
        _benchmark_analysis("opposite", "model-1", (-1.0, 0.0)),
        _benchmark_analysis("diagonal", "model-1", (1.0, 1.0)),
        _benchmark_analysis("aligned", "model-1", (2.0, 0.0)),
    )

    matches = rank_benchmark_matches(query, candidates)

    assert tuple(match.artwork_id for match in matches) == ("aligned", "diagonal", "opposite")
    assert tuple(match.similarity for match in matches) == pytest.approx((1.0, 2**-0.5, -1.0))


def test_rank_benchmark_matches_excludes_query_and_preserves_artwork_ids() -> None:
    query = _benchmark_analysis("query-id", "model-1", (1.0, 0.0))
    candidates = (
        _benchmark_analysis("query-id", "model-1", (1.0, 0.0)),
        _benchmark_analysis("candidate-id", "model-1", (0.0, 1.0)),
    )

    matches = rank_benchmark_matches(query, candidates)

    assert tuple(match.artwork_id for match in matches) == ("candidate-id",)


def test_rank_benchmark_matches_with_no_candidates() -> None:
    query = _benchmark_analysis("query", "model-1", (1.0, 0.0))

    assert rank_benchmark_matches(query, ()) == ()


def test_rank_benchmark_matches_with_only_query_candidate() -> None:
    query = _benchmark_analysis("query", "model-1", (1.0, 0.0))

    assert rank_benchmark_matches(query, (query,)) == ()


def test_rank_benchmark_matches_preserves_cosine_dimension_validation() -> None:
    query = _benchmark_analysis("query", "model-1", (1.0, 0.0))
    candidate = _benchmark_analysis("candidate", "model-1", (1.0,))

    with pytest.raises(ValueError, match="^Vectors must have the same dimensions\\.$"):
        rank_benchmark_matches(query, (candidate,))


def test_rank_benchmark_matches_keeps_model_results_separate() -> None:
    analyses = (
        _benchmark_analysis("query-2d", "model-2d", (1.0, 0.0)),
        _benchmark_analysis("candidate-2d", "model-2d", (0.0, 1.0)),
        _benchmark_analysis("query-3d", "model-3d", (1.0, 0.0, 0.0)),
        _benchmark_analysis("candidate-3d", "model-3d", (1.0, 0.0, 0.0)),
    )

    matches_2d = rank_benchmark_matches(analyses[0], (analyses[1],))
    matches_3d = rank_benchmark_matches(analyses[2], (analyses[3],))

    assert tuple(match.artwork_id for match in matches_2d) == ("candidate-2d",)
    assert tuple(match.artwork_id for match in matches_3d) == ("candidate-3d",)
    assert matches_2d[0].similarity == pytest.approx(0.0)
    assert matches_3d[0].similarity == pytest.approx(1.0)
