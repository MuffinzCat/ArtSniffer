"""Evaluate service permissions for a normalised rating without authorising artwork processing.

This pure rule is independent of unconditional safety, profile preferences and destination
eligibility. Composing those gates and enforcing their execution order remains separate work.
"""

from dataclasses import dataclass
from enum import StrEnum

from artsniffer.content.rating import ContentRating
from artsniffer.content.service_permissions import ServiceContentPermissions


class ServiceContentPermissionReason(StrEnum):
    """Stable machine-readable reason for a service-content permission decision."""

    ALLOWED = "allowed"
    RATING_UNKNOWN = "rating_unknown"
    ADULT_CONTENT_DISABLED = "adult_content_disabled"


@dataclass(frozen=True)
class ServiceContentPermissionDecision:
    """Represent a service rating-rule outcome, not subject-bound analysis authorisation."""

    allowed: bool
    reason: ServiceContentPermissionReason

    def __post_init__(self) -> None:
        """Require a recognised reason and an exactly agreeing boolean outcome."""
        if not isinstance(self.reason, ServiceContentPermissionReason):
            raise ValueError(
                "Service content permission reason must be a ServiceContentPermissionReason."
            )
        if self.allowed is not (self.reason is ServiceContentPermissionReason.ALLOWED):
            raise ValueError(
                "Service content permission allowed flag must agree with the decision reason."
            )


def evaluate_service_content_permissions(
    permissions: ServiceContentPermissions,
    rating: ContentRating,
) -> ServiceContentPermissionDecision:
    """Reject UNKNOWN and require explicit service enablement for ADULT.

    GENERAL and MATURE pass this layer independently of adult enablement. Acceptance here does
    not imply safety clearance, profile acceptance or destination eligibility.
    """
    if not isinstance(permissions, ServiceContentPermissions):
        raise ValueError("Service content permissions must be a ServiceContentPermissions.")
    if not isinstance(rating, ContentRating):
        raise ValueError("Service content rating must be a ContentRating.")

    if rating is ContentRating.UNKNOWN:
        reason = ServiceContentPermissionReason.RATING_UNKNOWN
    elif rating is ContentRating.ADULT and not permissions.adult_content_enabled:
        reason = ServiceContentPermissionReason.ADULT_CONTENT_DISABLED
    else:
        reason = ServiceContentPermissionReason.ALLOWED

    return ServiceContentPermissionDecision(
        allowed=reason is ServiceContentPermissionReason.ALLOWED,
        reason=reason,
    )
