"""Tests for weighted visual-similarity recommendation scoring."""

import pytest

from artsniffer.analysis.artwork import ArtworkAnalysis
from artsniffer.profiles.reference import ProfileReferenceLink
from artsniffer.references.collection_artwork import CollectionArtworkLink
from artsniffer.visual_scoring import calculate_visual_similarity_score


def _reference_entry(
    artwork_id: str,
    embedding: tuple[float, ...],
    profile_weight: float = 1.0,
    artwork_weight: float = 1.0,
    collection_id: str = "reference-collection",
    model_id: str = "visual-model-v1",
) -> tuple[ArtworkAnalysis, ProfileReferenceLink, CollectionArtworkLink]:
    """Build a consistent reference analysis and its existing influence links."""
    return (
        ArtworkAnalysis(
            artwork_id=artwork_id,
            model_id=model_id,
            embedding=embedding,
        ),
        ProfileReferenceLink(
            profile_id="cosy-foxes",
            collection_id=collection_id,
            weight=profile_weight,
        ),
        CollectionArtworkLink(
            collection_id=collection_id,
            artwork_id=artwork_id,
            weight=artwork_weight,
        ),
    )


def _candidate(embedding: tuple[float, ...]) -> ArtworkAnalysis:
    """Build a candidate analysis using the shared test model version."""
    return ArtworkAnalysis(
        artwork_id="candidate-artwork",
        model_id="visual-model-v1",
        embedding=embedding,
    )


def test_identical_embedding_produces_full_visual_similarity() -> None:
    """An identical reference embedding maps to a visual score of one."""
    component = calculate_visual_similarity_score(
        _candidate((1.0, 0.0)),
        (_reference_entry("reference-1", (1.0, 0.0)),),
    )

    assert component.score == pytest.approx(1.0)


def test_opposite_embedding_produces_zero_visual_similarity() -> None:
    """An opposite reference embedding maps to a visual score of zero."""
    component = calculate_visual_similarity_score(
        _candidate((1.0, 0.0)),
        (_reference_entry("reference-1", (-1.0, 0.0)),),
    )

    assert component.score == pytest.approx(0.0)


def test_orthogonal_embedding_produces_half_visual_similarity() -> None:
    """An orthogonal reference embedding maps to a visual score of one half."""
    component = calculate_visual_similarity_score(
        _candidate((1.0, 0.0)),
        (_reference_entry("reference-1", (0.0, 1.0)),),
    )

    assert component.score == pytest.approx(0.5)


def test_non_trivial_cosine_similarity_is_mapped_to_normalised_score() -> None:
    """A cosine similarity of 0.8 is transformed to a visual score of 0.9."""
    component = calculate_visual_similarity_score(
        _candidate((1.0, 0.0)),
        (_reference_entry("reference-1", (0.8, 0.6)),),
    )

    assert component.score == pytest.approx(0.9)


def test_equally_weighted_references_produce_their_arithmetic_mean() -> None:
    """Equal reference weights produce the mean of their normalised similarities."""
    component = calculate_visual_similarity_score(
        _candidate((1.0, 0.0)),
        (
            _reference_entry("identical", (1.0, 0.0)),
            _reference_entry("orthogonal", (0.0, 1.0)),
        ),
    )

    assert component.score == pytest.approx((1.0 + 0.5) / 2.0)


def test_collection_artwork_weight_changes_the_weighted_result() -> None:
    """Artwork weight multiplies that reference's contribution in the collection."""
    component = calculate_visual_similarity_score(
        _candidate((1.0, 0.0)),
        (
            _reference_entry("identical", (1.0, 0.0), artwork_weight=3.0),
            _reference_entry("opposite", (-1.0, 0.0), artwork_weight=1.0),
        ),
    )

    assert component.score == pytest.approx((1.0 * 3.0 + 0.0 * 1.0) / 4.0)


def test_profile_reference_weight_changes_the_weighted_result() -> None:
    """Profile-reference weight changes the influence of its collection."""
    component = calculate_visual_similarity_score(
        _candidate((1.0, 0.0)),
        (
            _reference_entry("identical", (1.0, 0.0), profile_weight=3.0),
            _reference_entry("opposite", (-1.0, 0.0), profile_weight=1.0),
        ),
    )

    assert component.score == pytest.approx((1.0 * 3.0 + 0.0 * 1.0) / 4.0)


def test_profile_and_artwork_weights_combine_multiplicatively() -> None:
    """Each effective reference weight is the product of both link weights."""
    component = calculate_visual_similarity_score(
        _candidate((1.0, 0.0)),
        (
            _reference_entry(
                "identical",
                (1.0, 0.0),
                profile_weight=2.0,
                artwork_weight=3.0,
            ),
            _reference_entry(
                "opposite",
                (-1.0, 0.0),
                profile_weight=1.0,
                artwork_weight=2.0,
            ),
        ),
    )

    assert component.score == pytest.approx((1.0 * 6.0 + 0.0 * 2.0) / (6.0 + 2.0))


def test_reference_order_does_not_change_visual_score() -> None:
    """Changing the order of reference entries does not affect the weighted result."""
    candidate = _candidate((1.0, 0.0))
    references = (
        _reference_entry("identical", (1.0, 0.0), artwork_weight=2.0),
        _reference_entry("orthogonal", (0.0, 1.0), profile_weight=3.0),
        _reference_entry("opposite", (-1.0, 0.0)),
    )

    forward = calculate_visual_similarity_score(candidate, references)
    reversed_order = calculate_visual_similarity_score(
        candidate,
        tuple(reversed(references)),
    )

    assert reversed_order.score == pytest.approx(forward.score)


def test_visual_similarity_component_has_expected_name_and_default_weight() -> None:
    """The visual component has its stable name and default component weight."""
    component = calculate_visual_similarity_score(
        _candidate((1.0, 0.0)),
        (_reference_entry("reference-1", (1.0, 0.0)),),
    )

    assert component.name == "visual_similarity"
    assert component.weight == 1.0


def test_visual_scoring_does_not_mutate_candidate_or_reference_objects() -> None:
    """Scoring leaves the candidate analysis and supplied reference objects unchanged."""
    candidate = _candidate((1.0, 0.0))
    reference = _reference_entry(
        "reference-1",
        (0.0, 1.0),
        profile_weight=2.0,
        artwork_weight=3.0,
    )
    candidate_values = (candidate.artwork_id, candidate.model_id, candidate.embedding)
    reference_values = tuple(
        (
            analysis.artwork_id,
            analysis.model_id,
            analysis.embedding,
            profile_link.profile_id,
            profile_link.collection_id,
            profile_link.weight,
            artwork_link.collection_id,
            artwork_link.artwork_id,
            artwork_link.weight,
        )
        for analysis, profile_link, artwork_link in (reference,)
    )

    calculate_visual_similarity_score(candidate, (reference,))

    assert (candidate.artwork_id, candidate.model_id, candidate.embedding) == candidate_values
    assert (
        tuple(
            (
                analysis.artwork_id,
                analysis.model_id,
                analysis.embedding,
                profile_link.profile_id,
                profile_link.collection_id,
                profile_link.weight,
                artwork_link.collection_id,
                artwork_link.artwork_id,
                artwork_link.weight,
            )
            for analysis, profile_link, artwork_link in (reference,)
        )
        == reference_values
    )


def test_visual_scoring_rejects_empty_references() -> None:
    """At least one analysed reference is required."""
    with pytest.raises(ValueError) as error:
        calculate_visual_similarity_score(_candidate((1.0, 0.0)), ())

    assert str(error.value) == "At least one reference analysis is required."


def test_visual_scoring_rejects_reference_artwork_id_mismatch() -> None:
    """A reference analysis must identify the artwork linked to its collection."""
    analysis = ArtworkAnalysis(
        artwork_id="different-artwork",
        model_id="visual-model-v1",
        embedding=(1.0, 0.0),
    )
    profile_link = ProfileReferenceLink(
        profile_id="cosy-foxes",
        collection_id="reference-collection",
    )
    artwork_link = CollectionArtworkLink(
        collection_id="reference-collection",
        artwork_id="linked-artwork",
    )

    with pytest.raises(ValueError) as error:
        calculate_visual_similarity_score(
            _candidate((1.0, 0.0)),
            ((analysis, profile_link, artwork_link),),
        )

    assert str(error.value) == ("Reference analysis artwork ID must match collection artwork link.")


def test_visual_scoring_rejects_collection_id_mismatch() -> None:
    """Both links for a reference must identify the same collection."""
    analysis = ArtworkAnalysis(
        artwork_id="reference-1",
        model_id="visual-model-v1",
        embedding=(1.0, 0.0),
    )
    profile_link = ProfileReferenceLink(
        profile_id="cosy-foxes",
        collection_id="profile-collection",
    )
    artwork_link = CollectionArtworkLink(
        collection_id="artwork-collection",
        artwork_id="reference-1",
    )

    with pytest.raises(ValueError) as error:
        calculate_visual_similarity_score(
            _candidate((1.0, 0.0)),
            ((analysis, profile_link, artwork_link),),
        )

    assert str(error.value) == (
        "Profile reference collection ID must match collection artwork link."
    )


def test_visual_scoring_rejects_model_id_mismatch() -> None:
    """Candidate and reference embeddings must come from the same model."""
    reference = _reference_entry(
        "reference-1",
        (1.0, 0.0),
        model_id="different-model",
    )

    with pytest.raises(ValueError) as error:
        calculate_visual_similarity_score(_candidate((1.0, 0.0)), (reference,))

    assert str(error.value) == "Candidate and reference analyses must use the same model."


@pytest.mark.parametrize("invalid_weight", [float("inf"), float("nan")])
def test_visual_scoring_rejects_non_finite_effective_weight(
    invalid_weight: float,
) -> None:
    """A non-finite product of the existing link weights must be rejected."""
    reference = _reference_entry(
        "reference-1",
        (1.0, 0.0),
        profile_weight=invalid_weight,
    )

    with pytest.raises(ValueError) as error:
        calculate_visual_similarity_score(_candidate((1.0, 0.0)), (reference,))

    assert str(error.value) == "Effective reference weight must be finite."


def test_visual_scoring_rejects_overflowed_total_reference_weight() -> None:
    """A total that overflows while adding finite reference weights is rejected."""
    references = (
        _reference_entry("reference-1", (1.0, 0.0), profile_weight=1e308),
        _reference_entry("reference-2", (1.0, 0.0), profile_weight=1e308),
    )

    with pytest.raises(ValueError) as error:
        calculate_visual_similarity_score(_candidate((1.0, 0.0)), references)

    assert str(error.value) == "Total reference weight must be finite."


@pytest.mark.parametrize(
    ("reference_embedding", "message"),
    [
        ((1.0,), "Vectors must have the same dimensions."),
        ((0.0, 0.0), "Right vector must have non-zero magnitude."),
    ],
)
def test_visual_scoring_propagates_cosine_similarity_errors(
    reference_embedding: tuple[float, ...],
    message: str,
) -> None:
    """Invalid embedding comparisons retain the cosine function's error."""
    reference = _reference_entry("reference-1", reference_embedding)

    with pytest.raises(ValueError) as error:
        calculate_visual_similarity_score(_candidate((1.0, 0.0)), (reference,))

    assert str(error.value) == message
