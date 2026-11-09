from dataclasses import dataclass, field

from artsniffer.profiles.content_policy import (
    ProfileContentPolicy,
    default_profile_content_policy,
)


@dataclass
class RecommendationProfile:
    """Validate profile configuration after dataclass initialisation.

    This prevents invalid profiles from entering the rest of the application.
    """

    # Stable internal identity, independent of the user-facing label.
    id: str
    # Human-readable name presented to the user.
    name: str
    # Disabled profiles are excluded from producing recommendations.
    enabled: bool = True
    # Candidates must meet this minimum score to qualify for the profile.
    threshold: float = 0.75
    # Declarative rating policy; each profile gets its own safe-default instance. It is not
    # evaluated here, and adult support remains a separate service-level control.
    content_policy: ProfileContentPolicy = field(default_factory=default_profile_content_policy)

    def __post_init__(self) -> None:
        """Validate profile configuration immediately after initialisation.

        Invalid profiles are rejected before entering the rest of the application.
        """
        if not self.id.strip():
            raise ValueError("Profile ID must not be empty or whitespace.")
        if not self.name.strip():
            raise ValueError("Profile name must not be empty or whitespace.")
        if not (0.0 <= self.threshold <= 1.0):
            raise ValueError("Threshold must be between 0.0 and 1.0.")


@dataclass
class ProfileReferenceLink:
    """Link a recommendation profile to a reference collection with a relative weight."""

    # Identifies the recommendation profile influenced by this reference.
    profile_id: str
    # Identifies the artwork collection contributing to the profile.
    collection_id: str
    # Sets this collection's influence for the profile; 1.0 is normal influence.
    weight: float = 1.0

    def __post_init__(self) -> None:
        """Validate the profile-to-collection link."""
        if not self.profile_id.strip():
            raise ValueError("Profile ID must not be empty or whitespace.")
        if not self.collection_id.strip():
            raise ValueError("Collection ID must not be empty or whitespace.")
        if self.weight <= 0.0:
            raise ValueError("Weight must be greater than 0.0.")
