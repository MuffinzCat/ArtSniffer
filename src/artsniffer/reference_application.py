"""Application-level orchestration for configured reference libraries."""

from collections.abc import Callable, Sequence

from artsniffer.commands.reference_paths import ensure_output_outside_reference_root
from artsniffer.commands.safe_write import safe_write
from artsniffer.commands.snapshot_file import encode_snapshot, read_snapshot
from artsniffer.persistence.reference_artwork import ReferenceArtworkStore
from artsniffer.references.artwork import ArtworkRecord
from artsniffer.references.local_filesystem import LocalFilesystemReferenceProvider
from artsniffer.references.observation import (
    ReferenceItemChangeKind,
    ReferenceItemObservation,
    diff_reference_observations,
)
from artsniffer.references.snapshot_diff import ReferenceSnapshotChange, diff_reference_snapshots
from artsniffer.settings import ArtSnifferSettings


def inspect_sources(
    settings: ArtSnifferSettings,
) -> tuple[tuple[str, tuple[ReferenceItemObservation, ...]], ...]:
    """Observe each configured local reference library and group observations by source."""
    results = []
    for folder in settings.reference_libraries:
        provider = LocalFilesystemReferenceProvider(folder.source_id, folder.folder)
        observations = provider.observe()
        results.append((provider.source_id, observations))
    return tuple(results)


def synchronise_sources(
    settings: ArtSnifferSettings,
) -> tuple[tuple[str, tuple[ReferenceSnapshotChange, ...]], ...]:
    """Synchronise libraries in order, publishing each state before processing the next.

    A later failure does not roll back states already published.
    """
    results = []
    for library in settings.reference_libraries:
        for reference_library in settings.reference_libraries:
            ensure_output_outside_reference_root(reference_library.folder, library.state_file)
        state_existed = library.state_file.exists()
        if state_existed:
            previous_snapshot = read_snapshot(library.state_file)
            if previous_snapshot.source_id != library.source_id:
                raise ValueError("Snapshot source ID does not match library source ID.")
        else:
            previous_snapshot = None
        previous = previous_snapshot.items if previous_snapshot is not None else ()
        provider = LocalFilesystemReferenceProvider(library.source_id, library.folder)
        current = provider.observe()
        changes = diff_reference_snapshots(library.source_id, previous, current)
        safe_write(
            library.state_file,
            encode_snapshot(library.source_id, str(library.folder), current),
            overwrite=state_existed,
        )
        results.append((library.source_id, changes))
    return tuple(results)


def reconcile_reference_artwork(
    source_id: str,
    known_artworks: Sequence[ArtworkRecord],
    observations: Sequence[ReferenceItemObservation],
    allocate_artwork_id: Callable[[], str],
) -> tuple[ArtworkRecord, ...]:
    """Reconcile reference artwork based on known artworks and observations."""
    result = []
    changes = diff_reference_observations(source_id, known_artworks, observations)
    for change in changes:
        if change.kind is ReferenceItemChangeKind.ADDED:
            if change.observation is None:
                raise ValueError("An added change requires an observation.")
            artwork_id = allocate_artwork_id()
            result.append(
                ArtworkRecord(
                    artwork_id,
                    change.source_id,
                    change.source_item_id,
                    change.observation.content_hash,
                )
            )
        if change.kind is ReferenceItemChangeKind.CHANGED:
            if change.observation is None:
                raise ValueError("A changed change requires an observation.")
            if change.known_artwork is None:
                raise ValueError("A changed change requires a known artwork.")
            result.append(
                ArtworkRecord(
                    change.known_artwork.id,
                    change.source_id,
                    change.source_item_id,
                    change.observation.content_hash,
                )
            )
        if change.kind is ReferenceItemChangeKind.UNCHANGED:
            if change.known_artwork is None:
                raise ValueError("An unchanged change requires a known artwork.")
            result.append(change.known_artwork)
        if change.kind is ReferenceItemChangeKind.REMOVED:
            continue
    return tuple(result)


def reconcile_persistent_reference_artwork(
    store: ReferenceArtworkStore,
    source_id: str,
    observations: Sequence[ReferenceItemObservation],
    allocate_artwork_id: Callable[[], str],
) -> tuple[ArtworkRecord, ...]:
    """Reconcile current observations and persist the resulting artwork state."""
    known_artworks = store.get_for_source(source_id)
    reconciled = reconcile_reference_artwork(
        source_id,
        known_artworks,
        observations,
        allocate_artwork_id,
    )
    store.replace_for_source(source_id, reconciled)
    return reconciled
