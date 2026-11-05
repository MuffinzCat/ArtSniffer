"""Provider-neutral resolution of a profile's reference graph into scoring entries."""

from collections import defaultdict
from collections.abc import Sequence

from artsniffer.artwork_analysis import ArtworkAnalysis
from artsniffer.profiles.profile import RecommendationProfile
from artsniffer.profiles.reference import ProfileReferenceLink
from artsniffer.references.collection import ReferenceCollection
from artsniffer.references.collection_artwork import CollectionArtworkLink
from artsniffer.references.source import ReferenceSource

# Matches the entry shape accepted by calculate_visual_similarity_score.
type ResolvedReferenceEntry = tuple[ArtworkAnalysis, ProfileReferenceLink, CollectionArtworkLink]


def resolve_profile_references(
    profile: RecommendationProfile,
    profile_links: Sequence[ProfileReferenceLink],
    collections: Sequence[ReferenceCollection],
    sources: Sequence[ReferenceSource],
    collection_artwork_links: Sequence[CollectionArtworkLink],
    analyses: Sequence[ArtworkAnalysis],
    model_id: str,
) -> tuple[ResolvedReferenceEntry, ...]:
    """Resolve a profile's enabled references into visual-scoring entries.

    Entries follow the matching profile-link order, then collection-artwork-link order. The same
    artwork reached through different collections yields separate entries. Source provider kind
    and location are opaque; only identity and enabled state are used. Nothing is scored.
    """
    if not model_id.strip():
        raise ValueError("Model ID must not be empty or whitespace.")
    if not profile.enabled:
        return ()

    matching_links: list[ProfileReferenceLink] = []
    seen_collection_ids: set[str] = set()
    for link in profile_links:
        if link.profile_id != profile.id:
            continue
        if link.collection_id in seen_collection_ids:
            raise ValueError(
                f"Duplicate profile reference link for collection ID: {link.collection_id}."
            )
        seen_collection_ids.add(link.collection_id)
        matching_links.append(link)

    collections_by_id: dict[str, list[ReferenceCollection]] = defaultdict(list)
    for collection in collections:
        if collection.id in seen_collection_ids:
            collections_by_id[collection.id].append(collection)
    sources_by_id: dict[str, list[ReferenceSource]] = defaultdict(list)
    for source in sources:
        sources_by_id[source.id].append(source)

    selected_links: list[ProfileReferenceLink] = []
    for link in matching_links:
        found = collections_by_id.get(link.collection_id)
        if not found:
            raise ValueError(f"Reference collection not found: {link.collection_id}.")
        if len(found) > 1:
            raise ValueError(f"Duplicate reference collection ID: {link.collection_id}.")
        collection = found[0]
        if not collection.enabled:
            continue
        found_sources = sources_by_id.get(collection.source_id)
        if not found_sources:
            raise ValueError(f"Reference source not found: {collection.source_id}.")
        if len(found_sources) > 1:
            raise ValueError(f"Duplicate reference source ID: {collection.source_id}.")
        if found_sources[0].enabled:
            selected_links.append(link)

    selected_ids = {link.collection_id for link in selected_links}
    artwork_links_by_collection: dict[str, list[CollectionArtworkLink]] = defaultdict(list)
    seen_artwork_links: set[tuple[str, str]] = set()
    for artwork_link in collection_artwork_links:
        if artwork_link.collection_id not in selected_ids:
            continue
        key = (artwork_link.collection_id, artwork_link.artwork_id)
        if key in seen_artwork_links:
            raise ValueError(
                f"Duplicate collection artwork link for collection ID "
                f"{artwork_link.collection_id} and artwork ID: {artwork_link.artwork_id}."
            )
        seen_artwork_links.add(key)
        artwork_links_by_collection[artwork_link.collection_id].append(artwork_link)

    analyses_by_artwork: dict[str, list[ArtworkAnalysis]] = defaultdict(list)
    for analysis in analyses:
        if analysis.model_id == model_id:
            analyses_by_artwork[analysis.artwork_id].append(analysis)

    entries: list[ResolvedReferenceEntry] = []
    for link in selected_links:
        for artwork_link in artwork_links_by_collection.get(link.collection_id, ()):
            matches = analyses_by_artwork.get(artwork_link.artwork_id)
            if not matches:
                raise ValueError(
                    f"Analysis not found for artwork ID {artwork_link.artwork_id} "
                    f"and model ID: {model_id}."
                )
            if len(matches) > 1:
                raise ValueError(
                    f"Duplicate analysis for artwork ID {artwork_link.artwork_id} "
                    f"and model ID: {model_id}."
                )
            entries.append((matches[0], link, artwork_link))
    return tuple(entries)
