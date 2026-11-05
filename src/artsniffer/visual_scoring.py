"""Calculate explainable visual-similarity score components."""

from math import isfinite

from artsniffer.artwork_analysis import ArtworkAnalysis
from artsniffer.profiles.reference import ProfileReferenceLink
from artsniffer.recommendation_score import RecommendationScoreComponent
from artsniffer.references.collection_artwork import CollectionArtworkLink
from artsniffer.similarity import cosine_similarity

type _ReferenceEntry = tuple[
    ArtworkAnalysis,
    ProfileReferenceLink,
    CollectionArtworkLink,
]


def calculate_visual_similarity_score(
    candidate: ArtworkAnalysis,
    references: tuple[_ReferenceEntry, ...],
) -> RecommendationScoreComponent:
    """Return a weighted visual-similarity component for the supplied references."""
    if not references:
        raise ValueError("At least one reference analysis is required.")

    weighted_score = 0.0
    total_weight = 0.0

    for reference_analysis, profile_link, artwork_link in references:
        if reference_analysis.artwork_id != artwork_link.artwork_id:
            raise ValueError("Reference analysis artwork ID must match collection artwork link.")
        if profile_link.collection_id != artwork_link.collection_id:
            raise ValueError("Profile reference collection ID must match collection artwork link.")
        if candidate.model_id != reference_analysis.model_id:
            raise ValueError("Candidate and reference analyses must use the same model.")

        effective_weight = profile_link.weight * artwork_link.weight
        if not isfinite(effective_weight):
            raise ValueError("Effective reference weight must be finite.")

        similarity = cosine_similarity(candidate.embedding, reference_analysis.embedding)
        normalised_similarity = max(0.0, min(1.0, (similarity + 1.0) / 2.0))

        total_weight += effective_weight
        if not isfinite(total_weight):
            raise ValueError("Total reference weight must be finite.")
        weighted_score += normalised_similarity * effective_weight

    if total_weight == 0.0:
        raise ValueError("Total reference weight must be greater than 0.0.")

    score = max(0.0, min(1.0, weighted_score / total_weight))
    return RecommendationScoreComponent(name="visual_similarity", score=score)
