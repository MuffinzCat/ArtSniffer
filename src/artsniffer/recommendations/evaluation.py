"""Compose visual-similarity scoring and eligibility into one evaluation."""

from dataclasses import dataclass

from artsniffer.analysis.artwork import ArtworkAnalysis
from artsniffer.profiles.profile import ProfileReferenceLink, RecommendationProfile
from artsniffer.recommendations.candidate import RecommendationCandidate
from artsniffer.recommendations.composition import compose_recommendation_score
from artsniffer.recommendations.eligibility import (
    RecommendationEligibilityDecision,
    evaluate_recommendation_eligibility,
)
from artsniffer.recommendations.score import RecommendationScoreComponent
from artsniffer.recommendations.visual_scoring import calculate_visual_similarity_score
from artsniffer.references.collection import CollectionArtworkLink


@dataclass
class RecommendationEvaluation:
    """Bundle a scored candidate, its eligibility decision, and score explanation."""

    candidate: RecommendationCandidate
    decision: RecommendationEligibilityDecision
    components: tuple[RecommendationScoreComponent, ...]


def evaluate_recommendation(
    profile: RecommendationProfile,
    candidate: ArtworkAnalysis,
    references: tuple[tuple[ArtworkAnalysis, ProfileReferenceLink, CollectionArtworkLink], ...],
) -> RecommendationEvaluation:
    """Score an artwork against profile references and decide its eligibility.

    Visual-scoring validation is allowed to propagate to the caller. The score components
    are retained on both the candidate and the evaluation to keep the result explainable.
    """
    visual_component = calculate_visual_similarity_score(candidate, references)
    components = (visual_component,)
    score = compose_recommendation_score(components)
    scored_candidate = RecommendationCandidate(profile.id, candidate.artwork_id, score, components)
    # Apply profile eligibility only after the candidate has its composed score.
    decision = evaluate_recommendation_eligibility(profile, scored_candidate)
    return RecommendationEvaluation(scored_candidate, decision, components)
