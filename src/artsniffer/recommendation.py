"""Already-scored recommendation candidates."""

from dataclasses import dataclass
from math import isfinite

from artsniffer.recommendation_score import RecommendationScoreComponent


@dataclass
class RecommendationCandidate:
    """Represent a scored artwork candidate for one recommendation profile."""

    # Identifies the profile for which this artwork was evaluated.
    profile_id: str
    # Identifies the discovered artwork being considered.
    artwork_id: str
    # Final normalised score used for threshold comparison and ranking.
    score: float
    # Optional ordered breakdown retained to explain the final score.
    components: tuple[RecommendationScoreComponent, ...] = ()

    def __post_init__(self) -> None:
        """Validate candidate identifiers and its final normalised score."""
        if not self.profile_id.strip():
            raise ValueError("Profile ID must not be empty or whitespace.")
        if not self.artwork_id.strip():
            raise ValueError("Artwork ID must not be empty or whitespace.")
        if not isfinite(self.score):
            raise ValueError("Recommendation score must be finite.")
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("Recommendation score must be between 0.0 and 1.0.")
