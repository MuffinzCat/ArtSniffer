"""Provider-neutral observation and comparison of reference item state."""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from artsniffer.artwork import ArtworkRecord


@dataclass(frozen=True)
class ReferenceItemObservation:
    """Describe one reference item currently reported by a source, using opaque identifiers."""

    # Identifies the configured reference source.
    source_id: str
    # Stable identifier assigned to the item by its provider.
    source_item_id: str
    # Identifies the currently observed content.
    content_hash: str

    def __post_init__(self) -> None:
        """Reject observations without the identifiers needed to compare them."""
        if not self.source_id.strip():
            raise ValueError("Source ID must not be empty or whitespace.")
        if not self.source_item_id.strip():
            raise ValueError("Source item ID must not be empty or whitespace.")
        if not self.content_hash.strip():
            raise ValueError("Content hash must not be empty or whitespace.")


class ReferenceItemChangeKind(StrEnum):
    """Classify how an observed reference item relates to known artwork state."""

    ADDED = "added"
    CHANGED = "changed"
    UNCHANGED = "unchanged"
    REMOVED = "removed"


@dataclass(frozen=True)
class ReferenceItemChange:
    """Describe one comparison result without allocating or altering any ArtworkRecord."""

    kind: ReferenceItemChangeKind
    source_id: str
    source_item_id: str
    # The previously known artwork; absent only for ADDED.
    known_artwork: ArtworkRecord | None
    # The current observation; absent only for REMOVED.
    observation: ReferenceItemObservation | None

    def __post_init__(self) -> None:
        """Reject contradictory kind, identity, and content combinations."""
        if not self.source_id.strip():
            raise ValueError("Source ID must not be empty or whitespace.")
        if not self.source_item_id.strip():
            raise ValueError("Source item ID must not be empty or whitespace.")

        needs_known = self.kind is not ReferenceItemChangeKind.ADDED
        needs_observation = self.kind is not ReferenceItemChangeKind.REMOVED
        if needs_known and self.known_artwork is None:
            raise ValueError(f"A {self.kind.value} change requires a known artwork.")
        if not needs_known and self.known_artwork is not None:
            raise ValueError(f"A {self.kind.value} change must not have a known artwork.")
        if needs_observation and self.observation is None:
            raise ValueError(f"A {self.kind.value} change requires an observation.")
        if not needs_observation and self.observation is not None:
            raise ValueError(f"A {self.kind.value} change must not have an observation.")

        for item in (self.known_artwork, self.observation):
            if item is None:
                continue
            if item.source_id != self.source_id or item.source_item_id != self.source_item_id:
                raise ValueError("Change identity must match its artwork and observation.")

        if self.known_artwork is not None and self.observation is not None:
            same_content = self.known_artwork.content_hash == self.observation.content_hash
            if self.kind is ReferenceItemChangeKind.UNCHANGED and not same_content:
                raise ValueError("An unchanged change requires matching content hashes.")
            if self.kind is ReferenceItemChangeKind.CHANGED and same_content:
                raise ValueError("A changed change requires differing content hashes.")


def diff_reference_observations(
    source_id: str,
    known_artworks: Sequence[ArtworkRecord],
    observations: Sequence[ReferenceItemObservation],
) -> tuple[ReferenceItemChange, ...]:
    """Compare known artwork with current observations for one source.

    Items match on source item ID only; content hashes merely separate unchanged from changed.
    Results follow observation order, then removals in known-artwork order. Nothing is mutated,
    persisted, or allocated.
    """
    if not source_id.strip():
        raise ValueError("Source ID must not be empty or whitespace.")

    known_by_item: dict[str, ArtworkRecord] = {}
    for artwork in known_artworks:
        if artwork.source_id != source_id:
            continue
        if artwork.source_item_id in known_by_item:
            raise ValueError(
                f"Duplicate known artwork for source item ID: {artwork.source_item_id}."
            )
        known_by_item[artwork.source_item_id] = artwork

    selected: list[ReferenceItemObservation] = []
    observed_ids: set[str] = set()
    for observation in observations:
        if observation.source_id != source_id:
            continue
        if observation.source_item_id in observed_ids:
            raise ValueError(
                f"Duplicate observation for source item ID: {observation.source_item_id}."
            )
        observed_ids.add(observation.source_item_id)
        selected.append(observation)

    changes: list[ReferenceItemChange] = []
    for observation in selected:
        known = known_by_item.get(observation.source_item_id)
        if known is None:
            kind = ReferenceItemChangeKind.ADDED
        elif known.content_hash == observation.content_hash:
            kind = ReferenceItemChangeKind.UNCHANGED
        else:
            kind = ReferenceItemChangeKind.CHANGED
        changes.append(
            ReferenceItemChange(kind, source_id, observation.source_item_id, known, observation)
        )
    for known in known_by_item.values():
        if known.source_item_id not in observed_ids:
            changes.append(
                ReferenceItemChange(
                    ReferenceItemChangeKind.REMOVED, source_id, known.source_item_id, known, None
                )
            )
    return tuple(changes)
