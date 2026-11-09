"""Stable result data for reference snapshot comparisons."""

from artsniffer.references.observation import ReferenceItemChangeKind
from artsniffer.references.snapshot_diff import ReferenceSnapshotChange


def count_changes(changes: tuple[ReferenceSnapshotChange, ...]) -> dict[str, int]:
    """Count each change kind in stable enum order."""
    counts = {kind.value: 0 for kind in ReferenceItemChangeKind}
    for change in changes:
        counts[change.kind.value] += 1
    return counts


def human_change_lines(changes: tuple[ReferenceSnapshotChange, ...]) -> list[str]:
    """Format category counts and changed item IDs in stable order."""
    counts = count_changes(changes)
    lines: list[str] = []
    for kind in ReferenceItemChangeKind:
        lines.append(f"{kind.value.title()}: {counts[kind.value]}")
        if kind is not ReferenceItemChangeKind.UNCHANGED:
            lines.extend(f"  {change.source_item_id}" for change in changes if change.kind is kind)
    return lines


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
