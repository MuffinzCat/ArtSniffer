"""Provider-neutral installation-level content permissions, separate from profile preferences."""

from dataclasses import dataclass
from enum import StrEnum

from artsniffer.content.rating import ContentRating


@dataclass(frozen=True)
class ServiceContentPermissions:
    """Declare installation permissions with adult content disabled unless explicitly enabled.

    These permissions do not configure unconditional safety, profile preferences or destination
    eligibility. Enabling adult content does not by itself authorise processing or delivery.
    """

    adult_content_enabled: bool = False

    def __post_init__(self) -> None:
        """Require explicit boolean enablement rather than coercing truthy configuration."""
        if not isinstance(self.adult_content_enabled, bool):
            raise ValueError("Service adult-content enablement must be a bool.")


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
