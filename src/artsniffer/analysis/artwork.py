"""Cached analysis data for artwork."""

from dataclasses import dataclass
from math import isfinite


@dataclass
class ArtworkAnalysis:
    """Store a model's cached visual representation and semantic labels for artwork."""

    # Identifies the artwork whose analysis is cached.
    artwork_id: str
    # Identifies the analysis or embedding model version used to produce this result.
    model_id: str
    # Compact visual representation used for later similarity comparisons.
    embedding: tuple[float, ...]
    # Optional semantic labels retained alongside the visual representation.
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Reject incomplete or non-finite cached analysis data."""
        if not self.artwork_id.strip():
            raise ValueError("Artwork ID must not be empty or whitespace.")
        if not self.model_id.strip():
            raise ValueError("Model ID must not be empty or whitespace.")
        if not self.embedding:
            raise ValueError("Embedding must contain at least one value.")
        if any(not isfinite(value) for value in self.embedding):
            raise ValueError("Embedding values must be finite.")
        if any(not tag.strip() for tag in self.tags):
            raise ValueError("Tag must not be empty or whitespace.")
