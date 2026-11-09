"""Provider-neutral snapshot comparisons, without persisted artwork identities."""

from dataclasses import FrozenInstanceError

import pytest

from artsniffer.references.observation import ReferenceItemChangeKind, ReferenceItemObservation
from artsniffer.references.snapshot_diff import ReferenceSnapshotChange, diff_reference_snapshots

ADDED = ReferenceItemChangeKind.ADDED
CHANGED = ReferenceItemChangeKind.CHANGED
UNCHANGED = ReferenceItemChangeKind.UNCHANGED
REMOVED = ReferenceItemChangeKind.REMOVED


def obs(item: str = "item", content: str = "hash", source: str = "source"):
    return ReferenceItemObservation(source, item, content)


@pytest.mark.parametrize(
    ("kind", "previous", "current"),
    [
        (ADDED, None, obs()),
        (REMOVED, obs(), None),
        (CHANGED, obs(), obs(content="new")),
        (UNCHANGED, obs(), obs()),
    ],
)
def test_result_preserves_observations_and_is_frozen(kind, previous, current):
    change = ReferenceSnapshotChange(kind, "source", "item", previous, current)
    assert change.kind is kind
    assert change.previous is previous
    assert change.current is current
    with pytest.raises(FrozenInstanceError):
        change.source_item_id = "other"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("kind", "previous", "current", "message"),
    [
        (ADDED, obs(), obs(), "An added change must not have a previous observation."),
        (ADDED, None, None, "An added change requires a current observation."),
        (REMOVED, None, None, "A removed change requires a previous observation."),
        (REMOVED, obs(), obs(), "A removed change must not have a current observation."),
        (CHANGED, None, obs(), "A changed change requires a previous observation."),
        (CHANGED, obs(), None, "A changed change requires a current observation."),
        (UNCHANGED, None, obs(), "An unchanged change requires a previous observation."),
        (UNCHANGED, obs(), None, "An unchanged change requires a current observation."),
        (CHANGED, obs(), obs(), "A changed change requires differing content hashes."),
        (
            UNCHANGED,
            obs(),
            obs(content="new"),
            "An unchanged change requires matching content hashes.",
        ),
    ],
)
def test_result_rejects_contradictory_sides_and_hashes(kind, previous, current, message):
    with pytest.raises(ValueError) as error:
        ReferenceSnapshotChange(kind, "source", "item", previous, current)
    assert str(error.value) == message


@pytest.mark.parametrize("kind", ["added", "unknown", None, 1])
def test_result_rejects_invalid_kind(kind):
    with pytest.raises(ValueError) as error:
        ReferenceSnapshotChange(kind, "source", "item", None, obs())
    assert str(error.value) == "Change kind must be a ReferenceItemChangeKind."


@pytest.mark.parametrize(
    ("source", "item", "message"),
    [
        (" \t", "item", "Source ID must not be empty or whitespace."),
        ("source", "", "Source item ID must not be empty or whitespace."),
    ],
)
def test_result_rejects_blank_identity(source, item, message):
    with pytest.raises(ValueError) as error:
        ReferenceSnapshotChange(ADDED, source, item, None, obs())
    assert str(error.value) == message


@pytest.mark.parametrize(
    ("kind", "previous", "current"),
    [
        (ADDED, None, obs(source="other")),
        (ADDED, None, obs(item="other")),
        (REMOVED, obs(source="other"), None),
        (REMOVED, obs(item="other"), None),
        (UNCHANGED, obs(item="other"), obs()),
        (UNCHANGED, obs(), obs(source="other")),
        (CHANGED, obs(source="other"), obs(content="new")),
        (CHANGED, obs(), obs(item="other", content="new")),
    ],
)
def test_result_rejects_mismatched_identity(kind, previous, current):
    with pytest.raises(ValueError) as error:
        ReferenceSnapshotChange(kind, "source", "item", previous, current)
    assert str(error.value) == "Change identity must match its observations."


def test_diff_empty_and_blank_source():
    assert diff_reference_snapshots("source", (), ()) == ()
    with pytest.raises(ValueError) as error:
        diff_reference_snapshots(" ", (), ())
    assert str(error.value) == "Source ID must not be empty or whitespace."


def test_diff_mixed_provider_order_sorted_removals_and_non_mutation():
    previous = [obs("z-removed"), obs("unchanged"), obs("changed"), obs("a-removed")]
    current = [obs("z-added"), obs("changed", "new"), obs("a-added"), obs("unchanged")]
    before_previous, before_current = list(previous), list(current)

    changes = diff_reference_snapshots("source", previous, current)

    assert isinstance(changes, tuple)
    assert [(change.kind, change.source_item_id) for change in changes] == [
        (ADDED, "z-added"),
        (CHANGED, "changed"),
        (ADDED, "a-added"),
        (UNCHANGED, "unchanged"),
        (REMOVED, "a-removed"),
        (REMOVED, "z-removed"),
    ]
    assert changes[1].previous is previous[2]
    assert changes[1].current is current[1]
    assert previous == before_previous
    assert current == before_current
    assert diff_reference_snapshots("source", list(reversed(previous)), current) == changes


@pytest.mark.parametrize("side", ["previous", "current"])
@pytest.mark.parametrize("hash_value", ["hash", "different"])
def test_diff_rejects_all_duplicate_ids(side, hash_value):
    duplicates = [obs(), obs(content=hash_value)]
    previous, current = (duplicates, []) if side == "previous" else ([], duplicates)
    with pytest.raises(ValueError) as error:
        diff_reference_snapshots("source", previous, current)
    assert str(error.value) == f"Duplicate {side} observation for source item ID: item."


@pytest.mark.parametrize("side", ["previous", "current"])
@pytest.mark.parametrize("source", ["Source", " source ", "other"])
def test_diff_rejects_wrong_source_without_filtering(side, source):
    wrong = [obs(source=source)]
    previous, current = (wrong, []) if side == "previous" else ([], wrong)
    with pytest.raises(ValueError) as error:
        diff_reference_snapshots("source", previous, current)
    assert (
        str(error.value) == f"{side.title()} observation source ID must match the requested source."
    )


def test_diff_preserves_exact_opaque_values_and_shared_hashes():
    source = " exact source "
    ids = [" Item ", "item", "ITEM", "\u00e9", "e\u0301", "../opaque"]
    previous = [obs(item, " HASH ", source) for item in ids]
    current = list(reversed(previous))
    changes = diff_reference_snapshots(source, previous, current)
    assert [change.source_item_id for change in changes] == list(reversed(ids))
    assert all(change.kind is UNCHANGED for change in changes)
    assert all(change.source_id == source for change in changes)
    assert all(change.current.content_hash == " HASH " for change in changes if change.current)


def test_diff_rename_is_added_and_removed_despite_shared_hash():
    changes = diff_reference_snapshots("source", [obs("old")], [obs("new")])
    assert [(change.kind, change.source_item_id) for change in changes] == [
        (ADDED, "new"),
        (REMOVED, "old"),
    ]


def test_diff_all_added_and_all_removed():
    items = [obs("z"), obs("a")]
    added = diff_reference_snapshots("source", [], items)
    removed = diff_reference_snapshots("source", items, [])
    assert [change.source_item_id for change in added] == ["z", "a"]
    assert all(change.kind is ADDED and change.previous is None for change in added)
    assert [change.source_item_id for change in removed] == ["a", "z"]
    assert all(change.kind is REMOVED and change.current is None for change in removed)
