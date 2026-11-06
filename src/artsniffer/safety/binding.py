"""Subject-bound safety evidence and evaluation results."""

from dataclasses import dataclass

from artsniffer.safety.authority import SafetyEvidenceAuthority
from artsniffer.safety.decision import SafetyGateDecision, SafetyGateReason
from artsniffer.safety.evaluation import evaluate_safety_evidence
from artsniffer.safety.evidence import SafetyEvidence
from artsniffer.safety.subject import SafetyClearedSubject, SafetySubject


@dataclass(frozen=True)
class BoundSafetyEvidence:
    """Associate one safety claim with an exact artwork and content version."""

    subject: SafetySubject
    evidence: SafetyEvidence

    def __post_init__(self) -> None:
        """Validate the subject and claim without changing either record."""
        if not isinstance(self.subject, SafetySubject):
            raise ValueError("Bound safety evidence subject must be a SafetySubject.")
        if not isinstance(self.evidence, SafetyEvidence):
            raise ValueError("Bound safety evidence claim must be a SafetyEvidence.")


@dataclass(frozen=True)
class SafetyEvaluationResult:
    """Bind an unconditional safety decision to its subject and criteria set."""

    subject: SafetySubject
    criteria_id: str
    decision: SafetyGateDecision

    def __post_init__(self) -> None:
        """Validate the subject, complete criteria ID, and evaluated decision."""
        if not isinstance(self.subject, SafetySubject):
            raise ValueError("Safety evaluation subject must be a SafetySubject.")
        if not isinstance(self.criteria_id, str) or not self.criteria_id.strip():
            raise ValueError("Safety evaluation criteria ID must not be empty or whitespace.")
        if not isinstance(self.decision, SafetyGateDecision):
            raise ValueError("Safety evaluation decision must be a SafetyGateDecision.")

    @property
    def cleared_subject(self) -> SafetyClearedSubject | None:
        """Return the downstream clearance token only for an affirmative decision."""
        if self.decision.reason is not SafetyGateReason.CLEARED or not self.decision.cleared:
            return None
        return SafetyClearedSubject(self.subject, self.criteria_id, self.decision)


def evaluate_bound_safety_evidence(
    subject: SafetySubject,
    evidence: tuple[BoundSafetyEvidence, ...],
    criteria_id: str,
    authorities: tuple[SafetyEvidenceAuthority, ...],
) -> SafetyEvaluationResult:
    """Evaluate claims only after verifying every binding matches the requested subject.

    Binding mismatches and duplicate claims are input-integrity errors. Empty evidence is valid
    input and produces the low-level evaluator's fail-closed insufficient-metadata decision.
    """
    if not isinstance(subject, SafetySubject):
        raise ValueError("Safety evaluation subject must be a SafetySubject.")

    claims: list[SafetyEvidence] = []
    seen: set[BoundSafetyEvidence] = set()
    for bound_evidence in evidence:
        if not isinstance(bound_evidence, BoundSafetyEvidence):
            raise ValueError("Safety evaluation evidence must contain BoundSafetyEvidence items.")
        if bound_evidence.subject != subject:
            raise ValueError("All bound safety evidence must match the requested subject.")
        if bound_evidence in seen:
            raise ValueError("Bound safety evidence must not contain duplicates.")
        seen.add(bound_evidence)
        claims.append(bound_evidence.evidence)

    decision = evaluate_safety_evidence(tuple(claims), criteria_id, authorities)
    return SafetyEvaluationResult(subject, criteria_id, decision)
