"""Compose unconditional safety clearance and rating rules before expensive analysis.

The safety gate remains independent and must already have produced a ``SafetyClearedSubject``.
This boundary then evaluates service permissions before profile policy, short-circuiting on
service rejection. Approval is limited to proceeding to analysis; it says nothing about
recommendation or destination eligibility.
"""

from dataclasses import dataclass
from enum import StrEnum

from artsniffer.content.rating import ContentRating
from artsniffer.content.service_permissions import (
    ServiceContentPermissionDecision,
    ServiceContentPermissionReason,
    ServiceContentPermissions,
    evaluate_service_content_permissions,
)
from artsniffer.profiles.content_policy import (
    ContentPolicyDecision,
    ContentPolicyReason,
    ProfileContentPolicy,
    evaluate_content_policy,
)
from artsniffer.safety.subject import SafetyClearedSubject


class PreAnalysisReason(StrEnum):
    """Stable machine-readable outcome for the pre-analysis boundary."""

    APPROVED = "approved"
    SERVICE_RATING_UNKNOWN = "service_rating_unknown"
    SERVICE_ADULT_CONTENT_DISABLED = "service_adult_content_disabled"
    PROFILE_RATING_ABOVE_MAXIMUM = "profile_rating_above_maximum"
    PROFILE_ADULT_REQUIRED = "profile_adult_required"


@dataclass(frozen=True)
class PreAnalysisDecision:
    """Represent whether a safety-cleared subject and rating may proceed to analysis."""

    reason: PreAnalysisReason

    def __post_init__(self) -> None:
        """Require a stable pre-analysis reason."""
        if not isinstance(self.reason, PreAnalysisReason):
            raise ValueError("Pre-analysis reason must be a PreAnalysisReason.")

    @property
    def approved(self) -> bool:
        """Return whether the decision permits proceeding to expensive analysis only."""
        return self.reason is PreAnalysisReason.APPROVED


_SERVICE_REJECTION_REASONS = {
    ServiceContentPermissionReason.RATING_UNKNOWN: PreAnalysisReason.SERVICE_RATING_UNKNOWN,
    ServiceContentPermissionReason.ADULT_CONTENT_DISABLED: (
        PreAnalysisReason.SERVICE_ADULT_CONTENT_DISABLED
    ),
}

_PROFILE_REASONS = {
    ContentPolicyReason.ALLOWED: PreAnalysisReason.APPROVED,
    ContentPolicyReason.RATING_ABOVE_MAXIMUM: PreAnalysisReason.PROFILE_RATING_ABOVE_MAXIMUM,
    ContentPolicyReason.ADULT_REQUIRED: PreAnalysisReason.PROFILE_ADULT_REQUIRED,
}


@dataclass(frozen=True)
class PreAnalysisResult:
    """Bind the pre-analysis decision and component outcomes to their exact subject and rating."""

    safety_cleared_subject: SafetyClearedSubject
    rating: ContentRating
    decision: PreAnalysisDecision
    service_decision: ServiceContentPermissionDecision
    profile_decision: ContentPolicyDecision | None

    def __post_init__(self) -> None:
        """Validate the subject-bound result and its service-first decision trace."""
        if not isinstance(self.safety_cleared_subject, SafetyClearedSubject):
            raise ValueError("Pre-analysis result requires a SafetyClearedSubject.")
        if not isinstance(self.rating, ContentRating):
            raise ValueError("Pre-analysis result rating must be a ContentRating.")
        if not isinstance(self.decision, PreAnalysisDecision):
            raise ValueError("Pre-analysis result decision must be a PreAnalysisDecision.")
        if not isinstance(self.service_decision, ServiceContentPermissionDecision):
            raise ValueError(
                "Pre-analysis result service decision must be a ServiceContentPermissionDecision."
            )

        if not self.service_decision.allowed:
            if self.profile_decision is not None:
                raise ValueError("Service rejection must not include a profile decision.")
            expected_reason = _SERVICE_REJECTION_REASONS.get(self.service_decision.reason)
        else:
            if not isinstance(self.profile_decision, ContentPolicyDecision):
                raise ValueError(
                    "Service acceptance requires a ContentPolicyDecision for the profile."
                )
            expected_reason = _PROFILE_REASONS.get(self.profile_decision.reason)

        if expected_reason is None or self.decision.reason is not expected_reason:
            raise ValueError("Pre-analysis reason must agree with component decisions.")

    @property
    def approved(self) -> bool:
        """Return whether this subject and rating may proceed to expensive analysis."""
        return self.decision.approved


def evaluate_pre_analysis(
    safety_cleared_subject: SafetyClearedSubject,
    rating: ContentRating,
    service_permissions: ServiceContentPermissions,
    profile_policy: ProfileContentPolicy,
) -> PreAnalysisResult:
    """Evaluate service permissions, then profile policy, for a safety-cleared subject.

    All arguments are validated before evaluation. A service rejection short-circuits the
    profile evaluator, so profile configuration cannot override installation-level rejection.
    """
    if not isinstance(safety_cleared_subject, SafetyClearedSubject):
        raise ValueError("Pre-analysis safety clearance must be a SafetyClearedSubject.")
    if not isinstance(rating, ContentRating):
        raise ValueError("Pre-analysis content rating must be a ContentRating.")
    if not isinstance(service_permissions, ServiceContentPermissions):
        raise ValueError("Pre-analysis service permissions must be a ServiceContentPermissions.")
    if not isinstance(profile_policy, ProfileContentPolicy):
        raise ValueError("Pre-analysis profile policy must be a ProfileContentPolicy.")

    service_decision = evaluate_service_content_permissions(service_permissions, rating)
    if not service_decision.allowed:
        reason = _SERVICE_REJECTION_REASONS[service_decision.reason]
        return PreAnalysisResult(
            safety_cleared_subject=safety_cleared_subject,
            rating=rating,
            decision=PreAnalysisDecision(reason),
            service_decision=service_decision,
            profile_decision=None,
        )

    profile_decision = evaluate_content_policy(profile_policy, rating)
    reason = _PROFILE_REASONS[profile_decision.reason]
    return PreAnalysisResult(
        safety_cleared_subject=safety_cleared_subject,
        rating=rating,
        decision=PreAnalysisDecision(reason),
        service_decision=service_decision,
        profile_decision=profile_decision,
    )
