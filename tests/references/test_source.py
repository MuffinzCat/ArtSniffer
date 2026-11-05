"""Tests for ArtSniffer reference sources."""

import pytest

from artsniffer.references.source import ReferenceSource


def test_reference_source_uses_required_values_and_defaults() -> None:
    """A valid source should preserve its identity and use the expected default."""

    # Create the smallest valid reference source.
    source = ReferenceSource(
        id="local-library",
        kind="local",
        location="C:/artwork",
    )

    # Required identity fields should be stored exactly as supplied.
    assert source.id == "local-library"
    assert source.kind == "local"
    assert source.location == "C:/artwork"

    # New sources should be enabled by default.
    assert source.enabled is True


def test_reference_source_preserves_disabled_state() -> None:
    """A source can be temporarily disabled without losing its configuration."""

    source = ReferenceSource(
        id="local-library",
        kind="local",
        location="C:/artwork",
        enabled=False,
    )

    assert source.enabled is False


@pytest.mark.parametrize("invalid_id", ["", " ", "   "])
def test_reference_source_rejects_empty_or_whitespace_id(invalid_id: str) -> None:
    """Source IDs must contain at least one non-whitespace character."""

    with pytest.raises(ValueError, match="Source ID must not be empty or whitespace"):
        ReferenceSource(
            id=invalid_id,
            kind="local",
            location="C:/artwork",
        )


@pytest.mark.parametrize("invalid_kind", ["", " ", "   "])
def test_reference_source_rejects_empty_or_whitespace_kind(invalid_kind: str) -> None:
    """Source kinds must contain at least one non-whitespace character."""

    with pytest.raises(ValueError, match="Source kind must not be empty or whitespace"):
        ReferenceSource(
            id="local-library",
            kind=invalid_kind,
            location="C:/artwork",
        )


@pytest.mark.parametrize("invalid_location", ["", " ", "   "])
def test_reference_source_rejects_empty_or_whitespace_location(
    invalid_location: str,
) -> None:
    """Source locations must contain at least one non-whitespace character."""

    with pytest.raises(
        ValueError,
        match="Source location must not be empty or whitespace",
    ):
        ReferenceSource(
            id="local-library",
            kind="local",
            location=invalid_location,
        )
