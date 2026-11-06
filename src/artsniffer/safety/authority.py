"""Authority grants for unconditional safety-evidence claims."""

from dataclasses import dataclass

from artsniffer.safety.evidence import (
    SafetyEvidenceAssertion,
    SafetyEvidenceMethod,
    SafetyEvidenceOrigin,
)


@dataclass(frozen=True)
class SafetyEvidenceAuthority:
    """Immutable authority grant for precisely scoped safety-evidence claims."""

    producer_id: str
    criteria_id: str
    origin: SafetyEvidenceOrigin
    method: SafetyEvidenceMethod
    allowed_assertions: frozenset[SafetyEvidenceAssertion]
    model_id: str | None = None
    model_version: str | None = None

    def __post_init__(self) -> None:
        """Validate the structure and scope of the authority grant."""
        if not isinstance(self.producer_id, str) or not self.producer_id.strip():
            raise ValueError(
                "Safety evidence authority producer ID must not be empty or whitespace."
            )
        if not isinstance(self.criteria_id, str) or not self.criteria_id.strip():
            raise ValueError(
                "Safety evidence authority criteria ID must not be empty or whitespace."
            )
        if not isinstance(self.origin, SafetyEvidenceOrigin):
            raise ValueError("Safety evidence authority origin must be a SafetyEvidenceOrigin.")
        if not isinstance(self.method, SafetyEvidenceMethod):
            raise ValueError("Safety evidence authority method must be a SafetyEvidenceMethod.")
        if not isinstance(self.allowed_assertions, frozenset):
            raise ValueError("Safety evidence authority allowed assertions must be a frozenset.")
        if not self.allowed_assertions:
            raise ValueError("Safety evidence authority allowed assertions must not be empty.")
        if any(
            not isinstance(assertion, SafetyEvidenceAssertion)
            for assertion in self.allowed_assertions
        ):
            raise ValueError(
                "Safety evidence authority allowed assertions must contain only "
                "SafetyEvidenceAssertion members."
            )
        if self.method is SafetyEvidenceMethod.MODEL:
            if not isinstance(self.model_id, str) or not self.model_id.strip():
                raise ValueError("Model authority requires a non-empty model ID.")
            if not isinstance(self.model_version, str) or not self.model_version.strip():
                raise ValueError("Model authority requires a non-empty model version.")
        else:
            if self.model_id is not None:
                raise ValueError(
                    "Model ID must be absent for non-model or unknown authority methods."
                )
            if self.model_version is not None:
                raise ValueError(
                    "Model version must be absent for non-model or unknown authority methods."
                )
