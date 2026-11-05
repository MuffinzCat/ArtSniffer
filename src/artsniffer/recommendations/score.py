"""Named contributions used to explain recommendation scores."""

from dataclasses import dataclass
from math import isfinite


@dataclass
class RecommendationScoreComponent:
    """Represent one weighted contribution to a recommendation score."""

    # Stable name identifying this contribution without restricting scoring strategies.
    name: str
    # Normalised score produced by this component.
    score: float
    # Relative influence when scoring; 1.0 represents normal influence.
    weight: float = 1.0

    def __post_init__(self) -> None:
        """Validate a component's name, normalised score, and relative weight."""
        if not self.name.strip():
            raise ValueError("Component name must not be empty or whitespace.")
        if not isfinite(self.score):
            raise ValueError("Component score must be finite.")
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("Component score must be between 0.0 and 1.0.")
        if not isfinite(self.weight):
            raise ValueError("Component weight must be finite.")
        if self.weight <= 0.0:
            raise ValueError("Component weight must be greater than 0.0.")
