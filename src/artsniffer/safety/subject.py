"""Provider-neutral artwork and content-version identity for safety evaluation."""

from dataclasses import dataclass

from artsniffer.safety.decision import SafetyGateDecision, SafetyGateReason


@dataclass(frozen=True)
class SafetySubject:
    """Identify one artwork and its exact, opaque content-version value."""

    artwork_id: str
    content_hash: str

    def __post_init__(self) -> None:
        """Validate identity values without normalising or recomputing them."""
        if not isinstance(self.artwork_id, str) or not self.artwork_id.strip():
            raise ValueError("Safety subject artwork ID must not be empty or whitespace.")
        if not isinstance(self.content_hash, str) or not self.content_hash.strip():
            raise ValueError("Safety subject content hash must not be empty or whitespace.")


@dataclass(frozen=True)
class SafetyClearedSubject:
    """Represent a subject cleared against one exact criteria set."""

    subject: SafetySubject
    criteria_id: str
    decision: SafetyGateDecision

    def __post_init__(self) -> None:
        """Require a valid subject, criteria ID, and affirmative safety decision."""
        if not isinstance(self.subject, SafetySubject):
            raise ValueError("Safety-cleared subject identity must be a SafetySubject.")
        if not isinstance(self.criteria_id, str) or not self.criteria_id.strip():
            raise ValueError("Safety-cleared subject criteria ID must not be empty or whitespace.")
        if (
            not isinstance(self.decision, SafetyGateDecision)
            or self.decision.reason is not SafetyGateReason.CLEARED
            or not self.decision.cleared
        ):
            raise ValueError("Safety-cleared subject requires a CLEARED safety gate decision.")
