"""Provider-neutral comparison of complete reference observation snapshots."""

from collections.abc import Sequence
from dataclasses import dataclass

from artsniffer.references.observation import (
    ReferenceItemChangeKind,
    ReferenceItemObservation,
)


@dataclass(frozen=True)
class ReferenceSnapshotChange:
    """Describe one difference between previous and current reference snapshots."""

    kind: ReferenceItemChangeKind
    source_id: str
    source_item_id: str
    previous: ReferenceItemObservation | None
    current: ReferenceItemObservation | None

    def __post_init__(self) -> None:
        """Reject contradictory change data."""
        if not isinstance(self.kind, ReferenceItemChangeKind):
            raise ValueError("Change kind must be a ReferenceItemChangeKind.")
        if not self.source_id.strip():
            raise ValueError("Source ID must not be empty or whitespace.")
        if not self.source_item_id.strip():
            raise ValueError("Source item ID must not be empty or whitespace.")
        match self.kind:
            case ReferenceItemChangeKind.ADDED:
                if self.previous is not None:
                    raise ValueError("An added change must not have a previous observation.")
                if self.current is None:
                    raise ValueError("An added change requires a current observation.")
            case ReferenceItemChangeKind.REMOVED:
                if self.previous is None:
                    raise ValueError("A removed change requires a previous observation.")
                if self.current is not None:
                    raise ValueError("A removed change must not have a current observation.")
            case ReferenceItemChangeKind.CHANGED:
                if self.previous is None:
                    raise ValueError("A changed change requires a previous observation.")
                if self.current is None:
                    raise ValueError("A changed change requires a current observation.")
                if self.previous.content_hash == self.current.content_hash:
                    raise ValueError("A changed change requires differing content hashes.")
            case ReferenceItemChangeKind.UNCHANGED:
                if self.previous is None:
                    raise ValueError("An unchanged change requires a previous observation.")
                if self.current is None:
                    raise ValueError("An unchanged change requires a current observation.")
                if self.previous.content_hash != self.current.content_hash:
                    raise ValueError("An unchanged change requires matching content hashes.")

        for observation in (self.previous, self.current):
            if observation is None:
                continue
            if (
                observation.source_id != self.source_id
                or observation.source_item_id != self.source_item_id
            ):
                raise ValueError("Change identity must match its observations.")


def diff_reference_snapshots(
    source_id: str,
    previous: Sequence[ReferenceItemObservation],
    current: Sequence[ReferenceItemObservation],
) -> tuple[ReferenceSnapshotChange, ...]:
    """Compare exact item IDs, preserving current order then sorting removals by ID.

    Both snapshots must contain unique items for exactly this source. Hashes distinguish
    changed from unchanged items, never identity. No input is mutated or artwork allocated.
    """
    if not source_id.strip():
        raise ValueError("Source ID must not be empty or whitespace.")

    previous_by_id: dict[str, ReferenceItemObservation] = {}
    current_by_id: dict[str, ReferenceItemObservation] = {}
    for label, snapshot, index in (
        ("Previous", previous, previous_by_id),
        ("Current", current, current_by_id),
    ):
        for observation in snapshot:
            if observation.source_id != source_id:
                raise ValueError(f"{label} observation source ID must match the requested source.")
            if observation.source_item_id in index:
                raise ValueError(
                    f"Duplicate {label.lower()} observation for source item ID: "
                    f"{observation.source_item_id}."
                )
            index[observation.source_item_id] = observation

    changes: list[ReferenceSnapshotChange] = []
    for item_id, observation in current_by_id.items():
        before = previous_by_id.get(item_id)
        if before is None:
            kind = ReferenceItemChangeKind.ADDED
        elif before.content_hash == observation.content_hash:
            kind = ReferenceItemChangeKind.UNCHANGED
        else:
            kind = ReferenceItemChangeKind.CHANGED
        changes.append(ReferenceSnapshotChange(kind, source_id, item_id, before, observation))

    for item_id in sorted(previous_by_id.keys() - current_by_id.keys()):
        changes.append(
            ReferenceSnapshotChange(
                ReferenceItemChangeKind.REMOVED,
                source_id,
                item_id,
                previous_by_id[item_id],
                None,
            )
        )
    return tuple(changes)
