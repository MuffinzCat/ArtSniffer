"""Storage-neutral interface for cached artwork analysis."""

from typing import Protocol

from artsniffer.analysis.artwork import ArtworkAnalysis


class AnalysisCache(Protocol):
    """Store analysis results by artwork, exact content version, and model version."""

    def get(
        self, artwork_id: str, content_hash: str, model_id: str
    ) -> ArtworkAnalysis | None:
        """Return the matching cached analysis, if one exists."""

    def put(self, analysis: ArtworkAnalysis, content_hash: str) -> None:
        """Store an analysis result for the supplied exact content version."""
