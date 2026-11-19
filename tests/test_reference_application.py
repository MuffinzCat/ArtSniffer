"""Tests for configured local-reference application orchestration."""

import hashlib
import os
from pathlib import Path
from unittest.mock import Mock

import pytest

from artsniffer import reference_application
from artsniffer.commands import safe_write as writer
from artsniffer.commands.snapshot_file import encode_snapshot, read_snapshot
from artsniffer.references.artwork import ArtworkRecord
from artsniffer.references.observation import ReferenceItemChangeKind, ReferenceItemObservation
from artsniffer.references.snapshot_diff import ReferenceSnapshotChange
from artsniffer.settings import ArtSnifferSettings, LocalReferenceLibrarySettings


def artwork(
    artwork_id: str,
    source_id: str,
    item_id: str,
    content_hash: str = "sha256:known",
) -> ArtworkRecord:
    return ArtworkRecord(artwork_id, source_id, item_id, content_hash)


def test_inspect_sources_with_no_libraries_does_not_construct_providers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected_provider(*args: object, **kwargs: object) -> None:
        pytest.fail("No provider should be created when no libraries are configured.")

    monkeypatch.setattr(
        reference_application, "LocalFilesystemReferenceProvider", unexpected_provider
    )

    assert reference_application.inspect_sources(ArtSnifferSettings(())) == ()


@pytest.mark.parametrize("source_ids", [("only",), ("first", "second", "third")])
def test_inspect_sources_observes_each_configured_provider_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, source_ids: tuple[str, ...]
) -> None:
    configured = tuple(
        LocalReferenceLibrarySettings(
            source_id=source_id,
            folder=tmp_path / f"library-{index}",
            state_file=tmp_path / f"state-{index}.json",
        )
        for index, source_id in enumerate(source_ids)
    )
    constructed: list[tuple[str, Path]] = []

    class StubProvider:
        def __init__(self, source_id: str, root: Path) -> None:
            self.source_id = source_id
            self.root = root
            self.index = len(providers)
            self.observe_calls = 0
            constructed.append((source_id, root))
            providers.append(self)

        def observe(self) -> tuple[ReferenceItemObservation, ...]:
            self.observe_calls += 1
            return tuple(
                ReferenceItemObservation(
                    self.source_id, f"{self.source_id}-{index}", f"hash-{index}"
                )
                for index in range(self.index + 1)
            )

    providers: list[StubProvider] = []
    monkeypatch.setattr(reference_application, "LocalFilesystemReferenceProvider", StubProvider)

    results = reference_application.inspect_sources(ArtSnifferSettings(configured))

    assert constructed == [(library.source_id, library.folder) for library in configured]
    assert [provider.observe_calls for provider in providers] == [1] * len(configured)
    assert tuple(source_id for source_id, _ in results) == source_ids
    for source_id, observations in results:
        assert all(observation.source_id == source_id for observation in observations)
        assert len(observations) == source_ids.index(source_id) + 1


def observation(source_id: str, item_id: str, content: bytes) -> ReferenceItemObservation:
    return ReferenceItemObservation(
        source_id, item_id, f"sha256:{hashlib.sha256(content).hexdigest()}"
    )


def test_synchronise_sources_with_no_libraries_does_no_work(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    constructor = Mock()
    safe_writer = Mock()
    monkeypatch.setattr(reference_application, "LocalFilesystemReferenceProvider", constructor)
    monkeypatch.setattr(reference_application, "safe_write", safe_writer)

    assert reference_application.synchronise_sources(ArtSnifferSettings(())) == ()
    constructor.assert_not_called()
    safe_writer.assert_not_called()


def test_synchronise_reads_and_replaces_complete_state_across_runs(tmp_path: Path) -> None:
    root = tmp_path / "library"
    root.mkdir()
    state = tmp_path / "state.json"
    settings = ArtSnifferSettings((LocalReferenceLibrarySettings("local", root, state),))
    for name, content in (
        ("changed.png", b"before"),
        ("removed.jpg", b"removed"),
        ("unchanged.webp", b"same"),
    ):
        (root / name).write_bytes(content)
    original = {
        "changed.png": observation("local", "changed.png", b"before"),
        "removed.jpg": observation("local", "removed.jpg", b"removed"),
        "unchanged.webp": observation("local", "unchanged.webp", b"same"),
    }

    first = reference_application.synchronise_sources(settings)

    assert first == (
        (
            "local",
            tuple(
                ReferenceSnapshotChange(ReferenceItemChangeKind.ADDED, "local", item_id, None, item)
                for item_id, item in original.items()
            ),
        ),
    )
    saved = read_snapshot(state)
    assert (saved.schema_version, saved.source_id, saved.root, saved.items) == (
        1,
        "local",
        str(root),
        tuple(original.values()),
    )

    second = reference_application.synchronise_sources(settings)
    assert second == (
        (
            "local",
            tuple(
                ReferenceSnapshotChange(
                    ReferenceItemChangeKind.UNCHANGED, "local", item_id, item, item
                )
                for item_id, item in original.items()
            ),
        ),
    )

    (root / "added.gif").write_bytes(b"added")
    (root / "changed.png").write_bytes(b"after")
    (root / "removed.jpg").unlink()
    added = observation("local", "added.gif", b"added")
    changed = observation("local", "changed.png", b"after")
    unchanged = original["unchanged.webp"]

    third = reference_application.synchronise_sources(settings)

    assert third == (
        (
            "local",
            (
                ReferenceSnapshotChange(
                    ReferenceItemChangeKind.ADDED, "local", "added.gif", None, added
                ),
                ReferenceSnapshotChange(
                    ReferenceItemChangeKind.CHANGED,
                    "local",
                    "changed.png",
                    original["changed.png"],
                    changed,
                ),
                ReferenceSnapshotChange(
                    ReferenceItemChangeKind.UNCHANGED,
                    "local",
                    "unchanged.webp",
                    unchanged,
                    unchanged,
                ),
                ReferenceSnapshotChange(
                    ReferenceItemChangeKind.REMOVED,
                    "local",
                    "removed.jpg",
                    original["removed.jpg"],
                    None,
                ),
            ),
        ),
    )
    assert read_snapshot(state).items == (added, changed, unchanged)
    assert (root / "added.gif").read_bytes() == b"added"
    assert (root / "changed.png").read_bytes() == b"after"
    assert (root / "unchanged.webp").read_bytes() == b"same"


def test_synchronise_empty_library_creates_empty_state(tmp_path: Path) -> None:
    root = tmp_path / "empty"
    root.mkdir()
    state = tmp_path / "state.json"
    settings = ArtSnifferSettings((LocalReferenceLibrarySettings("local", root, state),))

    assert reference_application.synchronise_sources(settings) == (("local", ()),)
    saved = read_snapshot(state)
    assert (saved.schema_version, saved.source_id, saved.root, saved.items) == (
        1,
        "local",
        str(root),
        (),
    )


@pytest.mark.parametrize("state_content", [b"{", b'{"source_id":"local"}'])
def test_synchronise_invalid_state_fails_before_provider_or_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, state_content: bytes
) -> None:
    root = tmp_path / "library"
    root.mkdir()
    state = tmp_path / "state.json"
    state.write_bytes(state_content)
    constructor = Mock()
    safe_writer = Mock()
    monkeypatch.setattr(reference_application, "LocalFilesystemReferenceProvider", constructor)
    monkeypatch.setattr(reference_application, "safe_write", safe_writer)

    with pytest.raises(ValueError):
        reference_application.synchronise_sources(
            ArtSnifferSettings((LocalReferenceLibrarySettings("local", root, state),))
        )

    assert state.read_bytes() == state_content
    constructor.assert_not_called()
    safe_writer.assert_not_called()


def test_synchronise_mismatched_source_fails_before_provider_or_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "library"
    root.mkdir()
    state = tmp_path / "state.json"
    original = encode_snapshot("other", str(root), ())
    state.write_bytes(original)
    constructor = Mock()
    safe_writer = Mock()
    monkeypatch.setattr(reference_application, "LocalFilesystemReferenceProvider", constructor)
    monkeypatch.setattr(reference_application, "safe_write", safe_writer)

    with pytest.raises(ValueError, match="source ID"):
        reference_application.synchronise_sources(
            ArtSnifferSettings((LocalReferenceLibrarySettings("local", root, state),))
        )

    assert state.read_bytes() == original
    constructor.assert_not_called()
    safe_writer.assert_not_called()


@pytest.mark.parametrize("stage", ["construct", "observe"])
def test_synchronise_provider_failure_preserves_existing_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, stage: str
) -> None:
    root = tmp_path / "library"
    root.mkdir()
    state = tmp_path / "state.json"
    original = encode_snapshot("local", str(root), (observation("local", "old.png", b"old"),))
    state.write_bytes(original)
    failure = OSError(f"{stage} failed")
    provider = Mock()
    constructor = Mock(return_value=provider)
    if stage == "construct":
        constructor.side_effect = failure
    else:
        provider.observe.side_effect = failure
    safe_writer = Mock()
    monkeypatch.setattr(reference_application, "LocalFilesystemReferenceProvider", constructor)
    monkeypatch.setattr(reference_application, "safe_write", safe_writer)

    with pytest.raises(OSError) as error:
        reference_application.synchronise_sources(
            ArtSnifferSettings((LocalReferenceLibrarySettings("local", root, state),))
        )

    assert error.value is failure
    assert state.read_bytes() == original
    safe_writer.assert_not_called()
    if stage == "construct":
        provider.observe.assert_not_called()
    else:
        provider.observe.assert_called_once_with()


def test_synchronise_encoding_failure_preserves_existing_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "library"
    root.mkdir()
    state = tmp_path / "state.json"
    original = encode_snapshot("local", str(root), (observation("local", "old.png", b"old"),))
    state.write_bytes(original)
    provider = Mock()
    provider.observe.return_value = (ReferenceItemObservation("local", "new.png", "invalid"),)
    monkeypatch.setattr(
        reference_application, "LocalFilesystemReferenceProvider", Mock(return_value=provider)
    )
    safe_writer = Mock()
    monkeypatch.setattr(reference_application, "safe_write", safe_writer)

    with pytest.raises(ValueError, match="content_hash"):
        reference_application.synchronise_sources(
            ArtSnifferSettings((LocalReferenceLibrarySettings("local", root, state),))
        )

    assert state.read_bytes() == original
    safe_writer.assert_not_called()


def test_synchronise_safe_write_failure_preserves_existing_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "library"
    root.mkdir()
    (root / "new.png").write_bytes(b"new")
    state = tmp_path / "state.json"
    original = encode_snapshot("local", str(root), (observation("local", "old.png", b"old"),))
    state.write_bytes(original)

    def fail_replace(source: str | os.PathLike[str], destination: str | os.PathLike[str]) -> None:
        raise OSError("replace failed")

    monkeypatch.setattr(writer.os, "replace", fail_replace)
    with pytest.raises(OSError, match="replace failed"):
        reference_application.synchronise_sources(
            ArtSnifferSettings((LocalReferenceLibrarySettings("local", root, state),))
        )

    assert state.read_bytes() == original
    assert list(tmp_path.glob(".state.json.*.tmp")) == []


def test_synchronise_rejects_state_inside_live_root_before_provider_or_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "library"
    root.mkdir()
    state = root / "state.json"
    constructor = Mock()
    safe_writer = Mock()
    monkeypatch.setattr(reference_application, "LocalFilesystemReferenceProvider", constructor)
    monkeypatch.setattr(reference_application, "safe_write", safe_writer)

    with pytest.raises(ValueError, match="outside the reference root"):
        reference_application.synchronise_sources(
            ArtSnifferSettings((LocalReferenceLibrarySettings("local", root, state),))
        )

    constructor.assert_not_called()
    safe_writer.assert_not_called()
    assert list(root.iterdir()) == []


def test_synchronise_rejects_state_inside_another_configured_library(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    first_root.mkdir()
    second_root.mkdir()
    state = second_root / "first-state.json"
    settings = ArtSnifferSettings(
        (
            LocalReferenceLibrarySettings("first", first_root, state),
            LocalReferenceLibrarySettings("second", second_root, tmp_path / "second-state.json"),
        )
    )
    provider = Mock()
    provider.observe.return_value = ()
    constructor = Mock(return_value=provider)
    safe_writer = Mock()
    monkeypatch.setattr(reference_application, "LocalFilesystemReferenceProvider", constructor)
    monkeypatch.setattr(reference_application, "safe_write", safe_writer)

    with pytest.raises(ValueError, match="outside the reference root"):
        reference_application.synchronise_sources(settings)

    constructor.assert_not_called()
    safe_writer.assert_not_called()
    assert list(second_root.iterdir()) == []


def test_synchronise_multiple_sources_uses_separate_state_in_configuration_order(
    tmp_path: Path,
) -> None:
    libraries = []
    for source_id in ("z-source", "a-source"):
        root = tmp_path / source_id
        root.mkdir()
        (root / "shared.png").write_bytes(source_id.encode())
        libraries.append(
            LocalReferenceLibrarySettings(source_id, root, tmp_path / f"{source_id}.json")
        )
    settings = ArtSnifferSettings(tuple(libraries))

    results = reference_application.synchronise_sources(settings)

    assert results == tuple(
        (
            library.source_id,
            (
                ReferenceSnapshotChange(
                    ReferenceItemChangeKind.ADDED,
                    library.source_id,
                    "shared.png",
                    None,
                    observation(library.source_id, "shared.png", library.source_id.encode()),
                ),
            ),
        )
        for library in libraries
    )
    for library in libraries:
        saved = read_snapshot(library.state_file)
        assert (saved.source_id, saved.root, saved.items) == (
            library.source_id,
            str(library.folder),
            (observation(library.source_id, "shared.png", library.source_id.encode()),),
        )

    repeated = reference_application.synchronise_sources(settings)
    assert tuple(source_id for source_id, _ in repeated) == ("z-source", "a-source")
    assert all(changes[0].kind is ReferenceItemChangeKind.UNCHANGED for _, changes in repeated)


def test_synchronise_later_failure_does_not_roll_back_earlier_publication(tmp_path: Path) -> None:
    libraries = []
    for source_id in ("first", "second", "third"):
        root = tmp_path / source_id
        root.mkdir()
        (root / "item.png").write_bytes(source_id.encode())
        libraries.append(
            LocalReferenceLibrarySettings(source_id, root, tmp_path / f"{source_id}.json")
        )
    first, second, third = libraries
    old_first = encode_snapshot("first", str(first.folder), ())
    first.state_file.write_bytes(old_first)
    invalid_second = encode_snapshot("other", str(second.folder), ())
    second.state_file.write_bytes(invalid_second)

    with pytest.raises(ValueError, match="source ID"):
        reference_application.synchronise_sources(ArtSnifferSettings(tuple(libraries)))

    assert first.state_file.read_bytes() != old_first
    assert read_snapshot(first.state_file).items == (observation("first", "item.png", b"first"),)
    assert second.state_file.read_bytes() == invalid_second
    assert not third.state_file.exists()


def test_reconcile_reference_artwork_handles_all_four_states() -> None:
    known = (
        artwork("art-unchanged", "source-a", "unchanged", "sha256:same"),
        artwork("art-changed", "source-a", "changed", "sha256:before"),
        artwork("art-removed", "source-a", "removed", "sha256:removed"),
    )
    observations = (
        ReferenceItemObservation("source-a", "unchanged", "sha256:same"),
        ReferenceItemObservation("source-a", "changed", "sha256:after"),
        ReferenceItemObservation("source-a", "added", "sha256:new"),
    )
    allocated: list[str] = []

    def allocate_artwork_id() -> str:
        allocated.append("art-added")
        return "art-added"

    result = reference_application.reconcile_reference_artwork(
        "source-a",
        known,
        observations,
        allocate_artwork_id,
    )

    assert result == (
        known[0],
        artwork("art-changed", "source-a", "changed", "sha256:after"),
        artwork("art-added", "source-a", "added", "sha256:new"),
    )
    assert allocated == ["art-added"]
    assert result[0] is known[0]
    assert all(record.source_item_id != "removed" for record in result)


def test_reconcile_reference_artwork_preserves_ids_for_changed_and_unchanged() -> None:
    known = (
        artwork("stable-added", "source-a", "unchanged", "sha256:same"),
        artwork("stable-changed", "source-a", "changed", "sha256:before"),
    )

    unchanged = reference_application.reconcile_reference_artwork(
        "source-a",
        known,
        (
            ReferenceItemObservation("source-a", "unchanged", "sha256:same"),
            ReferenceItemObservation("source-a", "changed", "sha256:after"),
        ),
        lambda: pytest.fail("Stable items must not allocate IDs"),
    )

    assert unchanged[0] is known[0]
    assert unchanged[1].id == "stable-changed"
    assert unchanged[1].content_hash == "sha256:after"

    twice = reference_application.reconcile_reference_artwork(
        "source-a",
        unchanged,
        (
            ReferenceItemObservation("source-a", "unchanged", "sha256:same"),
            ReferenceItemObservation("source-a", "changed", "sha256:after"),
        ),
        lambda: pytest.fail("Unchanged reconciled items must not allocate IDs"),
    )
    assert tuple(record.id for record in twice) == ("stable-added", "stable-changed")


def test_reconcile_allocates_only_for_genuinely_added_items() -> None:
    known = (
        artwork("art-same", "source-a", "same", "sha256:same"),
        artwork("art-changed", "source-a", "changed", "sha256:before"),
    )
    allocated: list[str] = []

    def allocate() -> str:
        allocated.append(f"art-new-{len(allocated) + 1}")
        return f"art-new-{len(allocated)}"

    result = reference_application.reconcile_reference_artwork(
        "source-a",
        known,
        (
            ReferenceItemObservation("source-a", "same", "sha256:same"),
            ReferenceItemObservation("source-a", "changed", "sha256:after"),
            ReferenceItemObservation("source-a", "new-one", "sha256:new-one"),
            ReferenceItemObservation("source-a", "new-two", "sha256:new-two"),
        ),
        allocate,
    )

    assert allocated == ["art-new-1", "art-new-2"]
    assert tuple(record.id for record in result) == (
        "art-same",
        "art-changed",
        "art-new-1",
        "art-new-2",
    )


def test_reconcile_removes_missing_items_and_keeps_source_scope() -> None:
    known = (
        artwork("art-local-kept", "source-a", "kept"),
        artwork("art-local-removed", "source-a", "removed"),
        artwork("art-other", "source-b", "kept"),
    )

    result = reference_application.reconcile_reference_artwork(
        "source-a",
        known,
        (
            ReferenceItemObservation("source-a", "kept", "sha256:known"),
            ReferenceItemObservation("source-b", "foreign", "sha256:foreign"),
        ),
        lambda: pytest.fail("Foreign observations must not allocate IDs"),
    )

    assert result == (known[0],)
    assert all(record.source_id == "source-a" for record in result)


class RecordingReferenceArtworkStore:
    def __init__(self, known: tuple[ArtworkRecord, ...]) -> None:
        self.known = known
        self.calls: list[object] = []

    def get_for_source(self, source_id: str) -> tuple[ArtworkRecord, ...]:
        self.calls.append(("get", source_id))
        return self.known

    def replace_for_source(
        self,
        source_id: str,
        artworks: object,
    ) -> None:
        self.calls.append(("replace", source_id, artworks))


def test_reconcile_persistent_loads_reconciles_replaces_and_returns_result() -> None:
    known = (
        artwork("art-same", "source-a", "same", "sha256:same"),
        artwork("art-changed", "source-a", "changed", "sha256:before"),
        artwork("art-removed", "source-a", "removed", "sha256:removed"),
    )
    store = RecordingReferenceArtworkStore(known)
    observations = (
        ReferenceItemObservation("source-a", "same", "sha256:same"),
        ReferenceItemObservation("source-a", "changed", "sha256:after"),
        ReferenceItemObservation("source-a", "added", "sha256:new"),
    )
    allocated: list[str] = []

    def allocate() -> str:
        allocated.append("art-added")
        return "art-added"

    result = reference_application.reconcile_persistent_reference_artwork(
        store,
        "source-a",
        observations,
        allocate,
    )

    assert result == (
        known[0],
        artwork("art-changed", "source-a", "changed", "sha256:after"),
        artwork("art-added", "source-a", "added", "sha256:new"),
    )
    assert allocated == ["art-added"]
    assert store.calls == [
        ("get", "source-a"),
        ("replace", "source-a", result),
    ]


def test_reconcile_persistent_empty_result_removes_source_state() -> None:
    store = RecordingReferenceArtworkStore((artwork("art-old", "source-a", "old"),))

    result = reference_application.reconcile_persistent_reference_artwork(
        store,
        "source-a",
        (),
        lambda: pytest.fail("No observation should be added"),
    )

    assert result == ()
    assert store.calls == [
        ("get", "source-a"),
        ("replace", "source-a", ()),
    ]
