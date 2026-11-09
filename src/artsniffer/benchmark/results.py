"""Path-free reports for one model's visual benchmark results.

Compare models using rankings, human judgements and within-model separation, not
their raw cosine similarities. Reports contain no embeddings, tags or source paths.
"""

import json
from dataclasses import asdict, dataclass
from math import isfinite

from artsniffer.benchmark.analysis import BenchmarkAnalysis
from artsniffer.benchmark.ranking import BenchmarkMatch, rank_benchmark_matches


@dataclass(frozen=True)
class BenchmarkImageResult:
    """Record inference timing for an artwork identified without a source path."""

    artwork_id: str
    elapsed_seconds: float


@dataclass(frozen=True)
class BenchmarkSeparation:
    """Record a caller-selected strong-minus-weak comparison within one model."""

    strong_expected_match_id: str
    weak_expected_match_id: str
    value: float


@dataclass(frozen=True)
class BenchmarkResult:
    """Store one model's dataset timings and visual ranking for one query.

    Embedding dimensions apply to the query and every dataset analysis. Images retain
    dataset order; matches retain ranking order. An empty dataset has no images or matches.
    """

    model_id: str
    embedding_dimensions: int
    query_artwork_id: str
    images: tuple[BenchmarkImageResult, ...]
    matches: tuple[BenchmarkMatch, ...]
    separation: BenchmarkSeparation | None = None

    def to_json(self) -> str:
        """Return deterministic, finite JSON ready for a caller to write locally."""
        return json.dumps(asdict(self), indent=2, allow_nan=False)


def build_benchmark_result(
    query: BenchmarkAnalysis,
    analyses: tuple[BenchmarkAnalysis, ...],
    *,
    separation_pair: tuple[str, str] | None = None,
) -> BenchmarkResult:
    """Build a report from one model's analyses without running inference or file I/O.

    Include the query in analyses to retain its dataset timing; it is excluded from
    matches. IDs must be stable artwork identifiers, not filesystem paths.
    Optional separation_pair supplies (strong_expected_match_id, weak_expected_match_id).
    Both must occur in the ranking. Expectations are caller-owned, never runner defaults.
    """
    dimensions = len(query.analysis.embedding)
    for analysis in (query, *analyses):
        if analysis.model_id != query.model_id or analysis.analysis.model_id != query.model_id:
            raise ValueError("All benchmark analyses must use the query model ID.")
        if analysis.artwork_id != analysis.analysis.artwork_id:
            raise ValueError("Analysis artwork ID must match benchmark artwork ID.")
        if len(analysis.analysis.embedding) != dimensions:
            raise ValueError("All benchmark embeddings must have the query dimensions.")
        if not isfinite(analysis.elapsed_seconds) or analysis.elapsed_seconds < 0.0:
            raise ValueError("Inference timing must be finite and non-negative.")
    if len({analysis.artwork_id for analysis in analyses}) != len(analyses):
        raise ValueError("Dataset artwork IDs must be unique.")

    matches = rank_benchmark_matches(query, analyses)
    separation = None
    if separation_pair is not None:
        strong_id, weak_id = separation_pair
        if strong_id == weak_id:
            raise ValueError("Separation requires two distinct artwork IDs.")
        similarities = {match.artwork_id: match.similarity for match in matches}
        if strong_id not in similarities or weak_id not in similarities:
            raise ValueError("Both separation artwork IDs must occur in the ranking.")
        separation = BenchmarkSeparation(
            strong_expected_match_id=strong_id,
            weak_expected_match_id=weak_id,
            value=similarities[strong_id] - similarities[weak_id],
        )

    return BenchmarkResult(
        model_id=query.model_id,
        embedding_dimensions=dimensions,
        query_artwork_id=query.artwork_id,
        images=tuple(
            BenchmarkImageResult(analysis.artwork_id, analysis.elapsed_seconds)
            for analysis in analyses
        ),
        matches=matches,
        separation=separation,
    )
