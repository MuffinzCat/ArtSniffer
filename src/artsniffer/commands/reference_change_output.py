"""Stable result data for reference snapshot comparisons."""

from artsniffer.references.observation import ReferenceItemChangeKind
from artsniffer.references.snapshot_diff import ReferenceSnapshotChange


def count_changes(changes: tuple[ReferenceSnapshotChange, ...]) -> dict[str, int]:
    """Count each change kind in stable enum order."""
    counts = {kind.value: 0 for kind in ReferenceItemChangeKind}
    for change in changes:
        counts[change.kind.value] += 1
    return counts


def changes_as_json(changes: tuple[ReferenceSnapshotChange, ...]) -> list[dict[str, object]]:
    """Represent every ordered change, including the absent side of additions/removals."""
    return [
        {
            "kind": change.kind.value,
            "source_item_id": change.source_item_id,
            "previous_content_hash": (
                change.previous.content_hash if change.previous is not None else None
            ),
            "current_content_hash": (
                change.current.content_hash if change.current is not None else None
            ),
        }
        for change in changes
    ]
