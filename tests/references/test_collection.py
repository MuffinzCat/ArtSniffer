"""Tests for ArtSniffer reference collections."""

import pytest

from artsniffer.references.collection import ReferenceCollection


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
