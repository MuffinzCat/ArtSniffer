"""Rank benchmark analyses by cosine similarity within a compatible model's results."""

from dataclasses import dataclass

from artsniffer.analysis.embedding_similarity import cosine_similarity
from artsniffer.benchmark.analysis import BenchmarkAnalysis


@dataclass
class BenchmarkMatch:
    """Identify a ranked artwork and its cosine similarity to the query."""

    artwork_id: str
    similarity: float


def rank_benchmark_matches(
    query: BenchmarkAnalysis,
    candidates: tuple[BenchmarkAnalysis, ...],
) -> tuple[BenchmarkMatch, ...]:
    """Return candidates from most to least similar, excluding the query artwork.

    The query and candidates should use the same model; scores from different models
    are not comparable. Embedding validation is delegated to :func:`cosine_similarity`.
    """
    matches: list[BenchmarkMatch] = []
    for candidate in candidates:
        if candidate.artwork_id == query.artwork_id:
            continue
        similarity = cosine_similarity(query.analysis.embedding, candidate.analysis.embedding)
        matches.append(BenchmarkMatch(artwork_id=candidate.artwork_id, similarity=similarity))
    matches.sort(key=lambda match: match.similarity, reverse=True)
    return tuple(matches)
