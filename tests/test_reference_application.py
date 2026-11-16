"""Tests for configured local-reference application orchestration."""

from pathlib import Path

import pytest

from artsniffer import reference_application
from artsniffer.references.observation import ReferenceItemObservation
from artsniffer.settings import ArtSnifferSettings, LocalReferenceLibrarySettings


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
