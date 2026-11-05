"""Tests for cached ArtSniffer artwork analysis."""

import pytest

from artsniffer.artwork_analysis import ArtworkAnalysis


def test_artwork_analysis_preserves_all_values() -> None:
    """A valid analysis should preserve its identifiers, embedding, and tags."""

    analysis = ArtworkAnalysis(
        artwork_id="artwork-001",
        model_id="visual-model-v2",
        embedding=(-1.5, 0.0, 2.25),
        tags=("watercolour", "landscape"),
    )

    assert analysis.artwork_id == "artwork-001"
    assert analysis.model_id == "visual-model-v2"
    assert analysis.embedding == (-1.5, 0.0, 2.25)
    assert analysis.tags == ("watercolour", "landscape")


def test_artwork_analysis_defaults_to_no_tags() -> None:
    """Tags should default to an empty tuple when none are supplied."""

    analysis = ArtworkAnalysis(
        artwork_id="artwork-001",
        model_id="visual-model-v2",
        embedding=(0.25,),
    )

    assert analysis.tags == ()


@pytest.mark.parametrize("invalid_artwork_id", ["", " ", "   "])
def test_artwork_analysis_rejects_empty_or_whitespace_artwork_id(
    invalid_artwork_id: str,
) -> None:
    """Artwork IDs must contain at least one non-whitespace character."""

    with pytest.raises(
        ValueError,
        match=r"\AArtwork ID must not be empty or whitespace\.\Z",
    ):
        ArtworkAnalysis(
            artwork_id=invalid_artwork_id,
            model_id="visual-model-v2",
            embedding=(0.25,),
        )


@pytest.mark.parametrize("invalid_model_id", ["", " ", "   "])
def test_artwork_analysis_rejects_empty_or_whitespace_model_id(
    invalid_model_id: str,
) -> None:
    """Model IDs must contain at least one non-whitespace character."""

    with pytest.raises(
        ValueError,
        match=r"\AModel ID must not be empty or whitespace\.\Z",
    ):
        ArtworkAnalysis(
            artwork_id="artwork-001",
            model_id=invalid_model_id,
            embedding=(0.25,),
        )


def test_artwork_analysis_rejects_empty_embedding() -> None:
    """An analysis embedding must contain at least one value."""

    with pytest.raises(
        ValueError,
        match=r"\AEmbedding must contain at least one value\.\Z",
    ):
        ArtworkAnalysis(
            artwork_id="artwork-001",
            model_id="visual-model-v2",
            embedding=(),
        )


@pytest.mark.parametrize(
    "invalid_value",
    [float("inf"), float("-inf"), float("nan")],
    ids=["positive-infinity", "negative-infinity", "nan"],
)
def test_artwork_analysis_rejects_non_finite_embedding_values(
    invalid_value: float,
) -> None:
    """Embedding values must be finite to support similarity comparisons."""

    with pytest.raises(
        ValueError,
        match=r"\AEmbedding values must be finite\.\Z",
    ):
        ArtworkAnalysis(
            artwork_id="artwork-001",
            model_id="visual-model-v2",
            embedding=(invalid_value,),
        )


@pytest.mark.parametrize("embedding", [(-1.5, 0.0, 2.25), (0.0,), (-3.0,)])
def test_artwork_analysis_accepts_finite_embedding_values(
    embedding: tuple[float, ...],
) -> None:
    """Finite negative, zero, and positive embedding values should be accepted."""

    analysis = ArtworkAnalysis(
        artwork_id="artwork-001",
        model_id="visual-model-v2",
        embedding=embedding,
    )

    assert analysis.embedding == embedding


@pytest.mark.parametrize("invalid_tag", ["", " ", "   "])
def test_artwork_analysis_rejects_empty_or_whitespace_tag(invalid_tag: str) -> None:
    """Each supplied tag must contain at least one non-whitespace character."""

    with pytest.raises(
        ValueError,
        match=r"\ATag must not be empty or whitespace\.\Z",
    ):
        ArtworkAnalysis(
            artwork_id="artwork-001",
            model_id="visual-model-v2",
            embedding=(0.25,),
            tags=(invalid_tag,),
        )
