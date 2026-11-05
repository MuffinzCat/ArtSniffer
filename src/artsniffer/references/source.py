from dataclasses import dataclass


@dataclass
class ReferenceSource:
    # Stable internal identity for this source.
    id: str
    # Provider type, such as local storage or OneDrive.
    kind: str
    # Provider-specific location interpreted by the corresponding adapter.
    location: str
    # Keeps source configuration available when temporarily not in use.
    enabled: bool = True

    def __post_init__(self) -> None:
        """Validate source configuration immediately after initialisation.

        Invalid sources are rejected before entering the rest of the application.
        """
        if not self.id.strip():
            raise ValueError("Source ID must not be empty or whitespace.")
        if not self.kind.strip():
            raise ValueError("Source kind must not be empty or whitespace.")
        if not self.location.strip():
            raise ValueError("Source location must not be empty or whitespace.")
