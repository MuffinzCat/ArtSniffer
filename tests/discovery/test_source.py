"""Tests for ArtSniffer discovery sources."""

import pytest

from artsniffer.discovery.source import DiscoverySource


def test_discovery_source_uses_required_values_and_defaults() -> None:
    """A valid source should preserve its identity and use the enabled default."""

    source = DiscoverySource(
        id="art-discovery",
        kind="future-provider",
    )

    assert source.id == "art-discovery"
    assert source.kind == "future-provider"
    assert source.enabled is True


def test_discovery_source_preserves_disabled_state() -> None:
    """A configured source can be disabled without deleting its configuration."""

    source = DiscoverySource(
        id="art-discovery",
        kind="future-provider",
        enabled=False,
    )

    assert source.enabled is False


@pytest.mark.parametrize("invalid_id", ["", " ", "   "])
def test_discovery_source_rejects_empty_or_whitespace_id(invalid_id: str) -> None:
    """Discovery source IDs must contain a non-whitespace character."""

    with pytest.raises(
        ValueError,
        match=r"\ADiscovery source ID must not be empty or whitespace\.\Z",
    ):
        DiscoverySource(
            id=invalid_id,
            kind="future-provider",
        )


@pytest.mark.parametrize("invalid_kind", ["", " ", "   "])
def test_discovery_source_rejects_empty_or_whitespace_kind(invalid_kind: str) -> None:
    """Discovery source kinds must contain a non-whitespace character."""

    with pytest.raises(
        ValueError,
        match=r"\ADiscovery source kind must not be empty or whitespace\.\Z",
    ):
        DiscoverySource(
            id="art-discovery",
            kind=invalid_kind,
        )
