"""Records for completed benchmark analyses."""

from dataclasses import dataclass

from artsniffer.analysis.artwork import ArtworkAnalysis


@dataclass
class BenchmarkAnalysis:
    """Store an analysis and the time taken to produce it."""

    model_id: str
    artwork_id: str
    analysis: ArtworkAnalysis
    elapsed_seconds: float
