"""Application-level orchestration for configured reference libraries."""

from artsniffer.references.local_filesystem import LocalFilesystemReferenceProvider
from artsniffer.references.observation import ReferenceItemObservation
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
