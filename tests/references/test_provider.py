"""Tests for the provider-neutral reference observation protocol."""

import ast
from pathlib import Path

import pytest

from artsniffer.references.observation import (
    ReferenceItemChangeKind,
    ReferenceItemObservation,
    diff_reference_observations,
)
from artsniffer.references.provider import ReferenceProvider


class StubReferenceProvider:
    """Supply an in-memory snapshot without inheriting from the protocol."""

    def __init__(self, source_id: str, items: tuple[tuple[str, str], ...] = ()) -> None:
        self.source_id = source_id
        self._observations = tuple(
            ReferenceItemObservation(source_id, item_id, content_hash)
            for item_id, content_hash in items
        )

    def observe(self) -> tuple[ReferenceItemObservation, ...]:
        """Return the complete fixture snapshot in its supplied order."""
        return self._observations


@pytest.mark.parametrize(
    "items",
    [(), (("item-z", "hash-z"), ("item-a", "hash-a"))],
)
def test_provider_accepts_structural_implementation_and_tuple_snapshot(
    items: tuple[tuple[str, str], ...],
) -> None:
    provider: ReferenceProvider = StubReferenceProvider("source-1", items)

    snapshot = provider.observe()

    assert isinstance(snapshot, tuple)
    assert all(isinstance(item, ReferenceItemObservation) for item in snapshot)
    assert snapshot == tuple(
        ReferenceItemObservation("source-1", item_id, content_hash)
        for item_id, content_hash in items
    )


def test_provider_preserves_exact_source_item_and_content_identity() -> None:
    provider: ReferenceProvider = StubReferenceProvider(
        " Source-A ", ((" Item-Z\t", " SHA256:AbC "),)
    )

    (observation,) = provider.observe()

    assert provider.source_id == " Source-A "
    assert observation.source_id == " Source-A "
    assert observation.source_item_id == " Item-Z\t"
    assert observation.content_hash == " SHA256:AbC "


def test_providers_remain_independently_bound_to_their_sources() -> None:
    first: ReferenceProvider = StubReferenceProvider("source-1", (("item", "hash"),))
    second: ReferenceProvider = StubReferenceProvider("source-2", (("item", "hash"),))

    first_snapshot = first.observe()
    second_snapshot = second.observe()

    assert first.source_id == "source-1"
    assert second.source_id == "source-2"
    assert first_snapshot == (ReferenceItemObservation("source-1", "item", "hash"),)
    assert second_snapshot == (ReferenceItemObservation("source-2", "item", "hash"),)
    assert first.observe() == first_snapshot
    assert second.observe() == second_snapshot


def test_unchanged_snapshots_preserve_provider_order_and_shared_hashes() -> None:
    provider: ReferenceProvider = StubReferenceProvider(
        "source-1", (("item-z", "shared-hash"), ("item-a", "shared-hash"))
    )

    snapshot = provider.observe()

    assert snapshot == (
        ReferenceItemObservation("source-1", "item-z", "shared-hash"),
        ReferenceItemObservation("source-1", "item-a", "shared-hash"),
    )
    assert provider.observe() == snapshot


def test_snapshot_passes_directly_to_diff_preserving_observation_order() -> None:
    provider: ReferenceProvider = StubReferenceProvider(
        "source-1", (("item-z", "hash-z"), ("item-a", "hash-a"))
    )
    snapshot = provider.observe()

    changes = diff_reference_observations(provider.source_id, (), snapshot)

    assert tuple(change.source_item_id for change in changes) == ("item-z", "item-a")
    assert all(change.kind is ReferenceItemChangeKind.ADDED for change in changes)
    for change, observation in zip(changes, snapshot, strict=True):
        assert change.source_id == provider.source_id
        assert change.observation is observation


def test_provider_module_has_only_agreed_neutral_dependencies() -> None:
    module_path = (
        Path(__file__).resolve().parents[2] / "src" / "artsniffer" / "references" / "provider.py"
    )
    allowed_modules = {"typing", "artsniffer.references.observation"}

    for node in ast.walk(ast.parse(module_path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            assert node.module is not None
            modules = [node.module]
        else:
            continue
        for module in modules:
            assert module in allowed_modules, f"Unexpected dependency: {module}"
