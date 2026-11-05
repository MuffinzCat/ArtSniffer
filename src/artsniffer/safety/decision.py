"""Unconditional safety gate decision vocabulary.

The safety gate produces binary decisions about whether content passes unconditional safety
rejection criteria. These decisions cannot be overridden by profile configuration, rating
policies, global adult-support settings, or destination settings.
"""

from dataclasses import dataclass
from enum import StrEnum


class SafetyGateReason(StrEnum):
    """Reason for an unconditional safety gate decision.

    CLEARED:
        The unconditional safety gate produced a passing decision from validated safety
        evidence. This does not mean the content is GENERAL-rated, allowed by every profile,
        eligible for a destination, or recommendation-eligible.

    PROHIBITED:
        The unconditional safety gate rejected the content. No profile, rating policy, global
        adult setting or destination setting may override this decision.

    INSUFFICIENT_METADATA:
        Trustworthy evidence was insufficient to affirm safety clearance. This gate fails
        closed: absence of a known prohibition must never be treated as CLEARED.
    """

    CLEARED = "cleared"
    PROHIBITED = "prohibited"
    INSUFFICIENT_METADATA = "insufficient_metadata"


@dataclass(frozen=True)
class SafetyGateDecision:
    """Immutable unconditional safety gate decision.

    Represents a single binary decision about whether content passes unconditional safety
    rejection criteria.

    Attributes:
        cleared: Whether the decision is a safety clearance.
        reason: The reason for the decision.

    Invariant:
        cleared must be True exactly when reason is SafetyGateReason.CLEARED. Contradictory
        combinations raise a ValueError.
    """

    cleared: bool
    reason: SafetyGateReason

    def __post_init__(self) -> None:
        """Validate the invariant that cleared agrees with the reason."""
        cleared_expected = self.reason is SafetyGateReason.CLEARED
        if self.cleared is not cleared_expected:
            raise ValueError("Safety gate cleared flag must agree with the decision reason.")
