"""Pure evaluation of authorised unconditional safety evidence."""

from artsniffer.safety.authority import SafetyEvidenceAuthority
from artsniffer.safety.decision import SafetyGateDecision, SafetyGateReason
from artsniffer.safety.evidence import SafetyEvidence, SafetyEvidenceAssertion


def _is_evidence_authorised(
    evidence: SafetyEvidence,
    authority: SafetyEvidenceAuthority,
) -> bool:
    """Return whether one authority grant permits one evidence claim."""
    return (
        evidence.producer_id == authority.producer_id
        and evidence.criteria_id == authority.criteria_id
        and evidence.origin is authority.origin
        and evidence.method is authority.method
        and evidence.model_id == authority.model_id
        and evidence.model_version == authority.model_version
        and evidence.assertion in authority.allowed_assertions
    )


def evaluate_safety_evidence(
    evidence: tuple[SafetyEvidence, ...],
    criteria_id: str,
    authorities: tuple[SafetyEvidenceAuthority, ...],
) -> SafetyGateDecision:
    """Evaluate independently authorised claims for one complete safety criteria set.

    The caller must establish evidence provenance and bind all claims to the same artwork
    and content version. This function verifies neither. Unauthorised or criteria-mismatched
    claims are ignored; applicable prohibitions override clearance, otherwise evidence must
    affirmatively support clearance. Confidence does not influence this decision.
    """
    if not isinstance(criteria_id, str) or not criteria_id.strip():
        raise ValueError("Safety evaluation criteria ID must not be empty or whitespace.")

    supports_clearance = False
    for claim in evidence:
        if claim.criteria_id != criteria_id:
            continue
        if not any(_is_evidence_authorised(claim, authority) for authority in authorities):
            continue
        if claim.assertion is SafetyEvidenceAssertion.INDICATES_PROHIBITED:
            return SafetyGateDecision(False, SafetyGateReason.PROHIBITED)
        if claim.assertion is SafetyEvidenceAssertion.SUPPORTS_CLEARANCE:
            supports_clearance = True

    if supports_clearance:
        return SafetyGateDecision(True, SafetyGateReason.CLEARED)
    return SafetyGateDecision(False, SafetyGateReason.INSUFFICIENT_METADATA)
