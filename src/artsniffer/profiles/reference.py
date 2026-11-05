from dataclasses import dataclass


@dataclass
class ProfileReferenceLink:
    # Identifies the recommendation profile influenced by this reference.
    profile_id: str
    # Identifies the artwork collection contributing to the profile.
    collection_id: str
    # Sets this collection's influence for the profile; 1.0 is normal influence.
    weight: float = 1.0

    def __post_init__(self) -> None:
        """Validate link configuration immediately after initialisation.

        Invalid links are rejected before entering the rest of the application.
        """
        if not self.profile_id.strip():
            raise ValueError("Profile ID must not be empty or whitespace.")
        if not self.collection_id.strip():
            raise ValueError("Collection ID must not be empty or whitespace.")
        if self.weight <= 0.0:
            raise ValueError("Weight must be greater than 0.0.")
