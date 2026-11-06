"""Provider-neutral claims used as input to a future unconditional safety gate.

An evidence record is not a decision, proof of trust, or a verified artwork binding. An
empty collection and an explicit insufficient claim remain distinct. Neither establishes
clearance without a future evaluator and independently verified provenance.
"""

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite


class SafetyEvidenceAssertion(StrEnum):
    """Normalised safety claim made by one producer about one artwork.

    SUPPORTS_CLEARANCE is an affirmative claim that the artwork meets the entire identified
    criteria set, not a gate decision. Absence of a reported violation or predicted semantic
    tag is not such a claim. INDICATES_PROHIBITED claims at least one criterion is violated;
    it does not claim complete coverage. INSUFFICIENT explicitly reports that the producer
    cannot support either claim.

    None of these claims is a content rating, profile-policy result, recommendation
    eligibility result, or destination eligibility result.
    """

    SUPPORTS_CLEARANCE = "supports_clearance"
    INDICATES_PROHIBITED = "indicates_prohibited"
    INSUFFICIENT = "insufficient"


class SafetyEvidenceOrigin(StrEnum):
    """Origin of a claim, without implying trust or authority.

    SOURCE_METADATA covers metadata or labels from the artwork's source, including its
    moderation metadata. SAFETY_ANALYSIS is a direct safety analysis of the artwork.
    OTHER_MODERATION is another policy or moderation mechanism, such as a separate review body.
    """

    SOURCE_METADATA = "source_metadata"
    SAFETY_ANALYSIS = "safety_analysis"
    OTHER_MODERATION = "other_moderation"


class SafetyEvidenceMethod(StrEnum):
    """Method used to produce a claim, independent of its origin or authority.

    MODEL identifies a model-produced claim; NON_MODEL means no model was used. UNKNOWN means
    the method is not established, not that no model was used. UNKNOWN must not be used to
    conceal missing provenance for a known model.
    """

    MODEL = "model"
    NON_MODEL = "non_model"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class SafetyEvidence:
    """One producer's claim about an artwork against a complete safety criteria set.

    ``producer_id`` is an opaque, sufficiently namespaced producer or mechanism identifier,
    not proof of authenticity or authority. ``criteria_id`` identifies an immutable, versioned
    complete criteria set; changes to the set require a new identifier. This record cannot
    verify either identity, the producer's actual coverage, or the subject's identity.

    MODEL claims require the actual model identity and version and may include confidence in
    the assertion. Confidence is not necessarily calibrated, comparable across models, or
    sufficient to establish authority or clearance. Other methods must not invent model
    provenance. Subject binding, source provenance verification, and evaluation are deferred.
    """

    assertion: SafetyEvidenceAssertion
    origin: SafetyEvidenceOrigin
    producer_id: str
    criteria_id: str
    method: SafetyEvidenceMethod
    model_id: str | None = None
    model_version: str | None = None
    confidence: float | None = None

    def __post_init__(self) -> None:
        """Validate the structure of the claim without establishing its trustworthiness."""
        if not isinstance(self.assertion, SafetyEvidenceAssertion):
            raise ValueError("Safety evidence assertion must be a SafetyEvidenceAssertion.")
        if not isinstance(self.origin, SafetyEvidenceOrigin):
            raise ValueError("Safety evidence origin must be a SafetyEvidenceOrigin.")
        if not isinstance(self.producer_id, str) or not self.producer_id.strip():
            raise ValueError("Safety evidence producer ID must not be empty or whitespace.")
        if not isinstance(self.criteria_id, str) or not self.criteria_id.strip():
            raise ValueError("Safety evidence criteria ID must not be empty or whitespace.")
        if not isinstance(self.method, SafetyEvidenceMethod):
            raise ValueError("Safety evidence method must be a SafetyEvidenceMethod.")

        if self.method is SafetyEvidenceMethod.MODEL:
            if not isinstance(self.model_id, str) or not self.model_id.strip():
                raise ValueError("Model evidence requires a non-empty model ID.")
            if not isinstance(self.model_version, str) or not self.model_version.strip():
                raise ValueError("Model evidence requires a non-empty model version.")
            if self.confidence is not None and (
                isinstance(self.confidence, bool)
                or not isinstance(self.confidence, (int, float))
                or not 0.0 <= self.confidence <= 1.0
                or not isfinite(self.confidence)
            ):
                raise ValueError("Safety evidence confidence must be finite and between 0 and 1.")
        else:
            if self.model_id is not None:
                raise ValueError("Model ID must be absent for non-model or unknown methods.")
            if self.model_version is not None:
                raise ValueError("Model version must be absent for non-model or unknown methods.")
            if self.confidence is not None:
                raise ValueError("Confidence must be absent for non-model or unknown methods.")
