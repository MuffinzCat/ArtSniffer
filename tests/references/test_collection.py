"""Tests for ArtSniffer reference collections."""

import pytest

from artsniffer.references.collection import CollectionArtworkLink, ReferenceCollection


def test_reference_collection_uses_required_values_and_defaults() -> None:
    """A valid collection should preserve its identity and use the expected default."""

    # Create the smallest valid reference collection.
    collection = ReferenceCollection(
        id="favourite-art",
        name="Favourite Art",
        source_id="local-library",
    )

    # Required identity fields should be stored exactly as supplied.
    assert collection.id == "favourite-art"
    assert collection.name == "Favourite Art"
    assert collection.source_id == "local-library"

    # New collections should contribute reference artwork by default.
    assert collection.enabled is True


def test_reference_collection_preserves_disabled_state() -> None:
    """A collection can remain configured without contributing reference artwork."""

    collection = ReferenceCollection(
        id="favourite-art",
        name="Favourite Art",
        source_id="local-library",
        enabled=False,
    )

    assert collection.enabled is False


@pytest.mark.parametrize("invalid_id", ["", " ", "   "])
def test_reference_collection_rejects_empty_or_whitespace_id(invalid_id: str) -> None:
    """Collection IDs must contain at least one non-whitespace character."""

    with pytest.raises(ValueError, match="Collection ID must not be empty or whitespace"):
        ReferenceCollection(
            id=invalid_id,
            name="Favourite Art",
            source_id="local-library",
        )


@pytest.mark.parametrize("invalid_name", ["", " ", "   "])
def test_reference_collection_rejects_empty_or_whitespace_name(invalid_name: str) -> None:
    """Collection names must contain at least one non-whitespace character."""

    with pytest.raises(ValueError, match="Collection name must not be empty or whitespace"):
        ReferenceCollection(
            id="favourite-art",
            name=invalid_name,
            source_id="local-library",
        )


@pytest.mark.parametrize("invalid_source_id", ["", " ", "   "])
def test_reference_collection_rejects_empty_or_whitespace_source_id(
    invalid_source_id: str,
) -> None:
    """Collection source IDs must contain at least one non-whitespace character."""

    with pytest.raises(
        ValueError,
        match="Collection source ID must not be empty or whitespace",
    ):
        ReferenceCollection(
            id="favourite-art",
            name="Favourite Art",
            source_id=invalid_source_id,
        )


def test_collection_artwork_link_uses_required_values_and_default_weight() -> None:
    """A valid link should preserve its identifiers and use the default weight."""

    link = CollectionArtworkLink(
        collection_id="favourite-art",
        artwork_id="artwork-001",
    )

    assert link.collection_id == "favourite-art"
    assert link.artwork_id == "artwork-001"
    assert link.weight == 1.0


def test_collection_artwork_link_preserves_explicit_positive_weight() -> None:
    """A link should preserve a positive weight supplied for this artwork."""

    link = CollectionArtworkLink(
        collection_id="favourite-art",
        artwork_id="artwork-001",
        weight=2.5,
    )

    assert link.weight == 2.5


@pytest.mark.parametrize("invalid_collection_id", ["", " ", "   "])
def test_collection_artwork_link_rejects_empty_or_whitespace_collection_id(
    invalid_collection_id: str,
) -> None:
    """Collection IDs must contain at least one non-whitespace character."""

    with pytest.raises(
        ValueError,
        match=r"\ACollection ID must not be empty or whitespace\.\Z",
    ):
        CollectionArtworkLink(
            collection_id=invalid_collection_id,
            artwork_id="artwork-001",
        )


@pytest.mark.parametrize("invalid_artwork_id", ["", " ", "   "])
def test_collection_artwork_link_rejects_empty_or_whitespace_artwork_id(
    invalid_artwork_id: str,
) -> None:
    """Artwork IDs must contain at least one non-whitespace character."""

    with pytest.raises(
        ValueError,
        match=r"\AArtwork ID must not be empty or whitespace\.\Z",
    ):
        CollectionArtworkLink(
            collection_id="favourite-art",
            artwork_id=invalid_artwork_id,
        )


@pytest.mark.parametrize("invalid_weight", [0.0, -0.01, -1.0])
def test_collection_artwork_link_rejects_non_positive_weight(
    invalid_weight: float,
) -> None:
    """A collection membership weight must be greater than zero."""

    with pytest.raises(
        ValueError,
        match=r"\AWeight must be greater than 0\.0\.\Z",
    ):
        CollectionArtworkLink(
            collection_id="favourite-art",
            artwork_id="artwork-001",
            weight=invalid_weight,
        )
