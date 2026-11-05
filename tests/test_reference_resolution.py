"""Tests for provider-neutral profile reference resolution."""

import pytest

from artsniffer.artwork_analysis import ArtworkAnalysis
from artsniffer.profiles.profile import RecommendationProfile
from artsniffer.profiles.reference import ProfileReferenceLink
from artsniffer.reference_resolution import resolve_profile_references
from artsniffer.references.collection import ReferenceCollection
from artsniffer.references.collection_artwork import CollectionArtworkLink
from artsniffer.references.source import ReferenceSource
from artsniffer.visual_scoring import calculate_visual_similarity_score

MODEL = "model-v1"


def _profile(profile_id: str = "p1", enabled: bool = True) -> RecommendationProfile:
    return RecommendationProfile(id=profile_id, name="Profile", enabled=enabled)


def _link(collection_id: str, profile_id: str = "p1", weight: float = 1.0):
    return ProfileReferenceLink(profile_id=profile_id, collection_id=collection_id, weight=weight)


def _collection(collection_id: str, source_id: str = "s1", enabled: bool = True):
    return ReferenceCollection(
        id=collection_id, name=collection_id, source_id=source_id, enabled=enabled
    )


def _source(source_id: str = "s1", enabled: bool = True) -> ReferenceSource:
    return ReferenceSource(id=source_id, kind="opaque-kind", location="opaque", enabled=enabled)


def _art(collection_id: str, artwork_id: str, weight: float = 1.0) -> CollectionArtworkLink:
    return CollectionArtworkLink(collection_id=collection_id, artwork_id=artwork_id, weight=weight)


def _analysis(artwork_id: str, model_id: str = MODEL, x: float = 1.0) -> ArtworkAnalysis:
    return ArtworkAnalysis(artwork_id=artwork_id, model_id=model_id, embedding=(x, 0.0))


def test_resolves_single_reference_preserving_objects() -> None:
    link, art, analysis = _link("c1", weight=2.0), _art("c1", "a1", 3.0), _analysis("a1")
    result = resolve_profile_references(
        _profile(), [link], [_collection("c1")], [_source()], [art], [analysis], MODEL
    )
    assert isinstance(result, tuple)
    assert len(result) == 1
    assert result[0][0] is analysis
    assert result[0][1] is link
    assert result[0][2] is art


def test_multiple_collections_follow_link_then_artwork_order() -> None:
    l2, l1 = _link("c2"), _link("c1")
    arts = [_art("c1", "a1"), _art("c2", "a3"), _art("c1", "a2"), _art("c2", "a4")]
    analyses = [_analysis(a) for a in ("a4", "a3", "a2", "a1")]
    result = resolve_profile_references(
        _profile(),
        [l2, l1],
        [_collection("c1"), _collection("c2")],
        [_source()],
        arts,
        analyses,
        MODEL,
    )
    assert [(e[1].collection_id, e[2].artwork_id) for e in result] == [
        ("c2", "a3"),
        ("c2", "a4"),
        ("c1", "a1"),
        ("c1", "a2"),
    ]


def test_collection_shared_by_different_profiles() -> None:
    links = [_link("c1", "p1", 1.5), _link("c1", "p2", 4.0)]
    args = ([_collection("c1")], [_source()], [_art("c1", "a1")], [_analysis("a1")], MODEL)
    first = resolve_profile_references(_profile("p1"), links, *args)
    second = resolve_profile_references(_profile("p2"), links, *args)
    assert [e[1].weight for e in first] == [1.5]
    assert [e[1].weight for e in second] == [4.0]


def test_unrelated_profile_links_are_ignored_even_when_duplicated_or_dangling() -> None:
    links = [_link("c1"), _link("other", "p2"), _link("other", "p2"), _link("missing", "p3")]
    result = resolve_profile_references(
        _profile(),
        links,
        [_collection("c1")],
        [_source()],
        [_art("c1", "a1")],
        [_analysis("a1")],
        MODEL,
    )
    assert len(result) == 1


def test_disabled_profile_returns_empty_without_resolving() -> None:
    result = resolve_profile_references(
        _profile(enabled=False), [_link("missing")], [], [], [], [], MODEL
    )
    assert result == ()


@pytest.mark.parametrize(("collection_enabled", "source_enabled"), [(False, True), (True, False)])
def test_disabled_collection_or_source_contributes_nothing(
    collection_enabled: bool, source_enabled: bool
) -> None:
    result = resolve_profile_references(
        _profile(),
        [_link("c1")],
        [_collection("c1", enabled=collection_enabled)],
        [_source(enabled=source_enabled)],
        [_art("c1", "a1")],
        [],
        MODEL,
    )
    assert result == ()


def test_empty_selected_collection_returns_empty() -> None:
    result = resolve_profile_references(
        _profile(), [_link("c1")], [_collection("c1")], [_source()], [], [], MODEL
    )
    assert result == ()


def test_unselected_collection_artwork_links_are_ignored() -> None:
    arts = [_art("c1", "a1"), _art("c2", "a2"), _art("c2", "a2")]
    result = resolve_profile_references(
        _profile(),
        [_link("c1")],
        [_collection("c1"), _collection("c2")],
        [_source()],
        arts,
        [_analysis("a1")],
        MODEL,
    )
    assert [e[2].artwork_id for e in result] == ["a1"]


def test_missing_collection_raises() -> None:
    with pytest.raises(ValueError, match=r"^Reference collection not found: c1\.$"):
        resolve_profile_references(_profile(), [_link("c1")], [], [_source()], [], [], MODEL)


def test_missing_source_raises() -> None:
    with pytest.raises(ValueError, match=r"^Reference source not found: s1\.$"):
        resolve_profile_references(
            _profile(), [_link("c1")], [_collection("c1")], [], [], [], MODEL
        )


def test_missing_requested_model_analysis_raises() -> None:
    with pytest.raises(
        ValueError, match=r"^Analysis not found for artwork ID a1 and model ID: model-v1\.$"
    ):
        resolve_profile_references(
            _profile(),
            [_link("c1")],
            [_collection("c1")],
            [_source()],
            [_art("c1", "a1")],
            [_analysis("a1", model_id="other-model")],
            MODEL,
        )


def test_other_model_analyses_are_ignored() -> None:
    other = _analysis("a1", model_id="other-model")
    wanted = _analysis("a1")
    result = resolve_profile_references(
        _profile(),
        [_link("c1")],
        [_collection("c1")],
        [_source()],
        [_art("c1", "a1")],
        [other, wanted],
        MODEL,
    )
    assert result[0][0] is wanted


def test_duplicate_profile_link_raises() -> None:
    with pytest.raises(
        ValueError, match=r"^Duplicate profile reference link for collection ID: c1\.$"
    ):
        resolve_profile_references(
            _profile(), [_link("c1"), _link("c1", weight=2.0)], [], [], [], [], MODEL
        )


def test_duplicate_collection_artwork_link_raises() -> None:
    with pytest.raises(
        ValueError,
        match=r"^Duplicate collection artwork link for collection ID c1 and artwork ID: a1\.$",
    ):
        resolve_profile_references(
            _profile(),
            [_link("c1")],
            [_collection("c1")],
            [_source()],
            [_art("c1", "a1"), _art("c1", "a1", 2.0)],
            [_analysis("a1")],
            MODEL,
        )


def test_duplicate_matching_analysis_raises() -> None:
    with pytest.raises(
        ValueError, match=r"^Duplicate analysis for artwork ID a1 and model ID: model-v1\.$"
    ):
        resolve_profile_references(
            _profile(),
            [_link("c1")],
            [_collection("c1")],
            [_source()],
            [_art("c1", "a1")],
            [_analysis("a1"), _analysis("a1", x=2.0)],
            MODEL,
        )


def test_duplicate_collection_id_raises() -> None:
    with pytest.raises(ValueError, match=r"^Duplicate reference collection ID: c1\.$"):
        resolve_profile_references(
            _profile(),
            [_link("c1")],
            [_collection("c1"), _collection("c1")],
            [_source()],
            [],
            [],
            MODEL,
        )


def test_duplicate_source_id_raises() -> None:
    with pytest.raises(ValueError, match=r"^Duplicate reference source ID: s1\.$"):
        resolve_profile_references(
            _profile(), [_link("c1")], [_collection("c1")], [_source(), _source()], [], [], MODEL
        )


def test_unrelated_duplicate_collections_and_sources_are_ignored() -> None:
    result = resolve_profile_references(
        _profile(),
        [_link("c1")],
        [_collection("c1"), _collection("x", "sx"), _collection("x", "sx")],
        [_source(), _source("sx"), _source("sx")],
        [_art("c1", "a1")],
        [_analysis("a1")],
        MODEL,
    )
    assert len(result) == 1


def test_same_artwork_through_two_collections_yields_two_entries() -> None:
    analysis = _analysis("a1")
    result = resolve_profile_references(
        _profile(),
        [_link("c1", weight=1.0), _link("c2", weight=2.0)],
        [_collection("c1"), _collection("c2")],
        [_source()],
        [_art("c1", "a1", 0.5), _art("c2", "a1", 0.25)],
        [analysis],
        MODEL,
    )
    assert len(result) == 2
    assert [(e[1].collection_id, e[2].weight) for e in result] == [("c1", 0.5), ("c2", 0.25)]
    assert all(e[0] is analysis for e in result)


@pytest.mark.parametrize("model_id", ["", "   "])
def test_blank_model_id_raises(model_id: str) -> None:
    with pytest.raises(ValueError, match=r"^Model ID must not be empty or whitespace\.$"):
        resolve_profile_references(_profile(), [], [], [], [], [], model_id)


def test_inputs_are_not_mutated() -> None:
    links = [_link("c1")]
    resolve_profile_references(_profile(), links, [_collection("c1")], [_source()], [], [], MODEL)
    assert links == [_link("c1")]


def test_resolved_entries_feed_visual_scoring_directly() -> None:
    entries = resolve_profile_references(
        _profile(),
        [_link("c1")],
        [_collection("c1")],
        [_source()],
        [_art("c1", "a1")],
        [_analysis("a1")],
        MODEL,
    )
    component = calculate_visual_similarity_score(_analysis("candidate"), entries)
    assert component.score == pytest.approx(1.0)
