"""Synthetic tests for path-free, single-model benchmark reports."""

import json

import pytest

from artsniffer.analysis.artwork import ArtworkAnalysis
from artsniffer.benchmark.analysis import BenchmarkAnalysis
from artsniffer.benchmark.results import build_benchmark_result


def _analysis(
    artwork_id: str,
    embedding: tuple[float, ...],
    *,
    model_id: str = "model-1",
    elapsed_seconds: float = 0.25,
    tags: tuple[str, ...] = (),
) -> BenchmarkAnalysis:
    return BenchmarkAnalysis(
        model_id=model_id,
        artwork_id=artwork_id,
        analysis=ArtworkAnalysis(artwork_id, model_id, embedding, tags),
        elapsed_seconds=elapsed_seconds,
    )


def test_result_preserves_timings_dimensions_and_deterministic_rankings() -> None:
    query = _analysis("query", (1.0, 0.0), elapsed_seconds=0.5)
    analyses = (
        _analysis("weak", (-1.0, 0.0), elapsed_seconds=0.75),
        query,
        _analysis("strong", (2.0, 0.0), elapsed_seconds=0.125),
        _analysis("tied", (3.0, 0.0), elapsed_seconds=0.0),
    )

    result = build_benchmark_result(query, analyses)

    assert result.model_id == "model-1"
    assert result.query_artwork_id == "query"
    assert result.embedding_dimensions == 2
    assert tuple(image.artwork_id for image in result.images) == ("weak", "query", "strong", "tied")
    assert tuple(image.elapsed_seconds for image in result.images) == (0.75, 0.5, 0.125, 0.0)
    assert tuple(match.artwork_id for match in result.matches) == ("strong", "tied", "weak")
    assert tuple(match.similarity for match in result.matches) == pytest.approx((1.0, 1.0, -1.0))
    assert result.separation is None
    assert result.to_json() == build_benchmark_result(query, analyses).to_json()


def test_result_json_contains_only_report_fields_not_private_metadata() -> None:
    private_path = r"C:\private\synthetic-source.png"
    query = _analysis("query", (1.0, 0.0), tags=(private_path,))
    candidate = _analysis("candidate", (0.0, 1.0), tags=("/private/source.png",))

    exported = build_benchmark_result(query, (query, candidate)).to_json()

    assert json.loads(exported) == {
        "model_id": "model-1",
        "embedding_dimensions": 2,
        "query_artwork_id": "query",
        "images": [
            {"artwork_id": "query", "elapsed_seconds": 0.25},
            {"artwork_id": "candidate", "elapsed_seconds": 0.25},
        ],
        "matches": [{"artwork_id": "candidate", "similarity": 0.0}],
        "separation": None,
    }
    assert "private" not in exported
    assert 'embedding"' not in exported
    assert "tags" not in exported
    assert "image_path" not in exported


@pytest.mark.parametrize("mismatch", ["query-inner", "candidate-outer", "candidate-inner"])
def test_result_rejects_model_mismatches(mismatch: str) -> None:
    query = _analysis("query", (1.0, 0.0))
    candidate = _analysis("candidate", (1.0, 0.0))
    if mismatch == "query-inner":
        query.analysis.model_id = "other-model"
    elif mismatch == "candidate-outer":
        candidate.model_id = "other-model"
    else:
        candidate.analysis.model_id = "other-model"

    with pytest.raises(ValueError) as error:
        build_benchmark_result(query, (candidate,))

    assert str(error.value) == "All benchmark analyses must use the query model ID."


def test_result_checks_model_even_for_excluded_query_artwork() -> None:
    query = _analysis("query", (1.0, 0.0))
    other_model = _analysis("query", (1.0, 0.0), model_id="other-model")

    with pytest.raises(ValueError) as error:
        build_benchmark_result(query, (other_model,))

    assert str(error.value) == "All benchmark analyses must use the query model ID."


def test_result_rejects_incompatible_dimensions() -> None:
    query = _analysis("query", (1.0, 0.0))

    with pytest.raises(ValueError) as error:
        build_benchmark_result(query, (_analysis("candidate", (1.0,)),))

    assert str(error.value) == "All benchmark embeddings must have the query dimensions."


def test_result_propagates_cosine_validation() -> None:
    query = _analysis("query", (1.0, 0.0))

    with pytest.raises(ValueError) as error:
        build_benchmark_result(query, (_analysis("candidate", (0.0, 0.0)),))

    assert str(error.value) == "Right vector must have non-zero magnitude."


@pytest.mark.parametrize("elapsed_seconds", [-0.1, float("inf"), float("nan")])
def test_result_rejects_invalid_inference_timings(elapsed_seconds: float) -> None:
    query = _analysis("query", (1.0, 0.0))
    candidate = _analysis("candidate", (1.0, 0.0), elapsed_seconds=elapsed_seconds)

    with pytest.raises(ValueError) as error:
        build_benchmark_result(query, (candidate,))

    assert str(error.value) == "Inference timing must be finite and non-negative."


def test_result_rejects_inconsistent_artwork_ids() -> None:
    query = _analysis("query", (1.0, 0.0))
    candidate = _analysis("candidate", (1.0, 0.0))
    candidate.artwork_id = "different-id"

    with pytest.raises(ValueError) as error:
        build_benchmark_result(query, (candidate,))

    assert str(error.value) == "Analysis artwork ID must match benchmark artwork ID."


def test_result_rejects_duplicate_dataset_artwork_ids() -> None:
    query = _analysis("query", (1.0, 0.0))
    candidate = _analysis("candidate", (1.0, 0.0))

    with pytest.raises(ValueError) as error:
        build_benchmark_result(query, (candidate, candidate))

    assert str(error.value) == "Dataset artwork IDs must be unique."


@pytest.mark.parametrize(
    ("separation_pair", "expected"),
    [(("strong", "weak"), 2.0), (("weak", "strong"), -2.0)],
)
def test_result_calculates_and_exports_configurable_separation(
    separation_pair: tuple[str, str], expected: float
) -> None:
    query = _analysis("query", (1.0, 0.0))
    candidates = (_analysis("weak", (-1.0, 0.0)), _analysis("strong", (1.0, 0.0)))

    result = build_benchmark_result(query, candidates, separation_pair=separation_pair)

    assert result.separation is not None
    assert result.separation.value == pytest.approx(expected)
    assert json.loads(result.to_json())["separation"] == {
        "strong_expected_match_id": separation_pair[0],
        "weak_expected_match_id": separation_pair[1],
        "value": expected,
    }


@pytest.mark.parametrize(
    ("pair", "message"),
    [
        (("candidate", "candidate"), "Separation requires two distinct artwork IDs."),
        (("candidate", "missing"), "Both separation artwork IDs must occur in the ranking."),
        (("query", "candidate"), "Both separation artwork IDs must occur in the ranking."),
    ],
)
def test_result_rejects_invalid_separation_pairs(pair: tuple[str, str], message: str) -> None:
    query = _analysis("query", (1.0, 0.0))

    with pytest.raises(ValueError) as error:
        build_benchmark_result(query, (_analysis("candidate", (1.0, 0.0)),), separation_pair=pair)

    assert str(error.value) == message


@pytest.mark.parametrize("include_query", [False, True])
def test_result_exports_empty_rankings(include_query: bool) -> None:
    query = _analysis("query", (1.0, 0.0))
    analyses = (query,) if include_query else ()

    result = build_benchmark_result(query, analyses)
    exported = json.loads(result.to_json())

    assert result.embedding_dimensions == 2
    assert result.matches == ()
    assert exported["matches"] == []
    assert exported["separation"] is None
    assert len(exported["images"]) == int(include_query)


def test_empty_result_cannot_supply_separation() -> None:
    query = _analysis("query", (1.0, 0.0))

    with pytest.raises(ValueError) as error:
        build_benchmark_result(query, (), separation_pair=("strong", "weak"))

    assert str(error.value) == "Both separation artwork IDs must occur in the ranking."
