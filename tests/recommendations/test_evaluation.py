"""Tests for recommendation scoring and eligibility orchestration."""

import pytest

from artsniffer.analysis.artwork import ArtworkAnalysis
from artsniffer.profiles.profile import RecommendationProfile
from artsniffer.profiles.reference import ProfileReferenceLink
from artsniffer.recommendations.eligibility import RecommendationEligibilityReason
from artsniffer.recommendations.evaluation import (
    RecommendationEvaluation,
    evaluate_recommendation,
)
from artsniffer.references.collection_artwork import CollectionArtworkLink


def _reference_entry(
    artwork_id: str,
    embedding: tuple[float, ...],
    model_id: str = "visual-model-v1",
) -> tuple[ArtworkAnalysis, ProfileReferenceLink, CollectionArtworkLink]:
    """Build a reference analysis with matching profile and collection links."""
    collection_id = "reference-collection"
    return (
        ArtworkAnalysis(
            artwork_id=artwork_id,
            model_id=model_id,
            embedding=embedding,
        ),
        ProfileReferenceLink(
            profile_id="cosy-foxes",
            collection_id=collection_id,
        ),
        CollectionArtworkLink(
            collection_id=collection_id,
            artwork_id=artwork_id,
        ),
    )


def _candidate(model_id: str = "visual-model-v1") -> ArtworkAnalysis:
    """Build a candidate analysis using a selected visual model version."""
    return ArtworkAnalysis(
        artwork_id="candidate-artwork",
        model_id=model_id,
        embedding=(1.0, 0.0),
    )


def _profile(
    *,
    threshold: float = 0.4,
    enabled: bool = True,
) -> RecommendationProfile:
    """Build the profile evaluated by these orchestration tests."""
    return RecommendationProfile(
        id="cosy-foxes",
        name="Cosy Foxes",
        enabled=enabled,
        threshold=threshold,
    )


def test_evaluation_includes_visual_score_and_preserves_candidate_details() -> None:
    """The visual component contributes to the score and is retained in the result."""
    profile = _profile()
    artwork = _candidate()
    references = (_reference_entry("reference-artwork", (0.0, 1.0)),)

    evaluation = evaluate_recommendation(profile, artwork, references)

    assert isinstance(evaluation, RecommendationEvaluation)
    assert evaluation.candidate.profile_id == profile.id
    assert evaluation.candidate.artwork_id == artwork.artwork_id
    assert evaluation.candidate.score == pytest.approx(0.5)
    assert len(evaluation.components) == 1
    assert evaluation.components[0].name == "visual_similarity"
    assert evaluation.components[0].score == pytest.approx(0.5)
    assert evaluation.candidate.components is evaluation.components
    assert evaluation.decision.eligible is True
    assert evaluation.decision.reason is RecommendationEligibilityReason.ELIGIBLE


def test_below_threshold_evaluation_reports_expected_reason() -> None:
    """A low visual score is ineligible specifically because it misses the threshold."""
    evaluation = evaluate_recommendation(
        _profile(threshold=0.6),
        _candidate(),
        (_reference_entry("reference-artwork", (0.0, 1.0)),),
    )

    assert evaluation.decision.eligible is False
    assert evaluation.decision.reason is RecommendationEligibilityReason.BELOW_THRESHOLD


def test_disabled_profile_remains_ineligible_for_high_visual_score() -> None:
    """A disabled profile stays ineligible even when visual similarity is high."""
    evaluation = evaluate_recommendation(
        _profile(enabled=False),
        _candidate(),
        (_reference_entry("reference-artwork", (1.0, 0.0)),),
    )

    assert evaluation.candidate.score == pytest.approx(1.0)
    assert evaluation.decision.eligible is False
    assert evaluation.decision.reason is RecommendationEligibilityReason.PROFILE_DISABLED


def test_empty_references_propagate_visual_scoring_validation() -> None:
    """Evaluation does not bypass the visual scorer's required-reference validation."""
    with pytest.raises(
        ValueError,
        match=r"^At least one reference analysis is required\.$",
    ):
        evaluate_recommendation(_profile(), _candidate(), ())


def test_model_mismatch_propagates_visual_scoring_validation() -> None:
    """Evaluation does not bypass the visual scorer's model compatibility check."""
    with pytest.raises(
        ValueError,
        match=r"^Candidate and reference analyses must use the same model\.$",
    ):
        evaluate_recommendation(
            _profile(),
            _candidate(model_id="another-model"),
            (_reference_entry("reference-artwork", (1.0, 0.0)),),
        )
