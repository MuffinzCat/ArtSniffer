"""Run a synthetic recommendation evaluation without external services."""

from artsniffer.analysis.artwork import ArtworkAnalysis
from artsniffer.profiles.profile import ProfileReferenceLink, RecommendationProfile
from artsniffer.recommendations.evaluation import evaluate_recommendation
from artsniffer.references.collection import CollectionArtworkLink


def main() -> None:
    """Run the local synthetic recommendation and print its evaluation."""
    profile = RecommendationProfile(
        id="muffin",
        name="Muffin",
        threshold=0.75,
    )

    candidate = ArtworkAnalysis(
        artwork_id="candidate-001",
        model_id="demo-model",
        embedding=(0.8, 0.6, 0.2),
    )

    reference_analysis = ArtworkAnalysis(
        artwork_id="reference-001",
        model_id="demo-model",
        embedding=(0.75, 0.65, 0.25),
    )

    profile_link = ProfileReferenceLink(
        profile_id="muffin",
        collection_id="favourites",
    )

    artwork_link = CollectionArtworkLink(
        collection_id="favourites",
        artwork_id="reference-001",
    )

    references = ((reference_analysis, profile_link, artwork_link),)
    evaluation = evaluate_recommendation(profile, candidate, references)

    print("ArtSniffer local recommendation demo")
    print()
    print(f"Profile: {profile.name}")
    print(f"Artwork: {evaluation.candidate.artwork_id}")
    print(f"Score: {evaluation.candidate.score:.4f}")
    print(f"Eligible: {evaluation.decision.eligible}")
    print(f"Reason: {evaluation.decision.reason}")


if __name__ == "__main__":
    main()
