"""Provider-neutral installation-level content permissions, separate from profile preferences."""

from dataclasses import dataclass


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
