import pytest

from artsniffer.artwork import ArtworkRecord
from artsniffer.reference_observation import (
    ReferenceItemChange,
    ReferenceItemChangeKind,
    ReferenceItemObservation,
    diff_reference_observations,
)

ADDED = ReferenceItemChangeKind.ADDED
CHANGED = ReferenceItemChangeKind.CHANGED
UNCHANGED = ReferenceItemChangeKind.UNCHANGED
REMOVED = ReferenceItemChangeKind.REMOVED
IDENTITY_MESSAGE = "Change identity must match its artwork and observation."


def art(item: str, content: str = "h1", source: str = "s1", art_id: str | None = None):
    return ArtworkRecord(art_id or f"a-{source}-{item}", source, item, content)


def obs(item: str, content: str = "h1", source: str = "s1"):
    return ReferenceItemObservation(source, item, content)


def summary(changes):
    return [(c.kind, c.source_item_id) for c in changes]


class TestObservation:
    def test_valid(self):
        o = obs("i1")
        assert (o.source_id, o.source_item_id, o.content_hash) == ("s1", "i1", "h1")

    @pytest.mark.parametrize(
        ("args", "message"),
        [
            (("", "i", "h"), "Source ID must not be empty or whitespace."),
            (("  ", "i", "h"), "Source ID must not be empty or whitespace."),
            (("s", "", "h"), "Source item ID must not be empty or whitespace."),
            (("s", " ", "h"), "Source item ID must not be empty or whitespace."),
            (("s", "i", ""), "Content hash must not be empty or whitespace."),
            (("s", "i", "\t"), "Content hash must not be empty or whitespace."),
        ],
    )
    def test_rejects_blank(self, args, message):
        with pytest.raises(ValueError) as exc:
            ReferenceItemObservation(*args)
        assert str(exc.value) == message

    def test_immutable(self):
        with pytest.raises(AttributeError):
            obs("i1").content_hash = "x"  # type: ignore[misc]


class TestChange:
    def test_kind_values(self):
        assert [k.value for k in ReferenceItemChangeKind] == [
            "added",
            "changed",
            "unchanged",
            "removed",
        ]

    def test_valid_combinations(self):
        ReferenceItemChange(ADDED, "s1", "i", None, obs("i"))
        ReferenceItemChange(CHANGED, "s1", "i", art("i"), obs("i", "h2"))
        ReferenceItemChange(UNCHANGED, "s1", "i", art("i"), obs("i"))
        ReferenceItemChange(REMOVED, "s1", "i", art("i"), None)

    @pytest.mark.parametrize(
        ("kind", "known", "observation", "message"),
        [
            (ADDED, art("i"), obs("i"), "A added change must not have a known artwork."),
            (ADDED, None, None, "A added change requires an observation."),
            (CHANGED, None, obs("i", "h2"), "A changed change requires a known artwork."),
            (CHANGED, art("i"), None, "A changed change requires an observation."),
            (UNCHANGED, None, obs("i"), "A unchanged change requires a known artwork."),
            (UNCHANGED, art("i"), None, "A unchanged change requires an observation."),
            (REMOVED, None, None, "A removed change requires a known artwork."),
            (REMOVED, art("i"), obs("i"), "A removed change must not have an observation."),
            (CHANGED, art("i"), obs("i"), "A changed change requires differing content hashes."),
            (
                UNCHANGED,
                art("i"),
                obs("i", "h2"),
                "An unchanged change requires matching content hashes.",
            ),
            (UNCHANGED, art("j"), obs("i"), IDENTITY_MESSAGE),
            (ADDED, None, obs("i", source="s2"), IDENTITY_MESSAGE),
        ],
    )
    def test_rejects_contradictions(self, kind, known, observation, message):
        with pytest.raises(ValueError) as exc:
            ReferenceItemChange(kind, "s1", "i", known, observation)
        assert str(exc.value) == message

    def test_rejects_blank_identity(self):
        with pytest.raises(ValueError, match="Source ID must not be empty"):
            ReferenceItemChange(ADDED, " ", "i", None, obs("i"))
        with pytest.raises(ValueError, match="Source item ID must not be empty"):
            ReferenceItemChange(ADDED, "s1", " ", None, obs("i"))


class TestDiff:
    def test_blank_source(self):
        with pytest.raises(ValueError) as exc:
            diff_reference_observations(" ", [], [])
        assert str(exc.value) == "Source ID must not be empty or whitespace."

    def test_empty(self):
        assert diff_reference_observations("s1", [], []) == ()

    def test_added_only(self):
        result = diff_reference_observations("s1", [], [obs("a"), obs("b")])
        assert isinstance(result, tuple)
        assert summary(result) == [(ADDED, "a"), (ADDED, "b")]
        assert all(c.known_artwork is None for c in result)

    def test_unchanged(self):
        known, o = art("a"), obs("a")
        (change,) = diff_reference_observations("s1", [known], [o])
        assert change.kind is UNCHANGED
        assert change.known_artwork is known and change.observation is o

    def test_changed(self):
        known, o = art("a"), obs("a", "h2")
        (change,) = diff_reference_observations("s1", [known], [o])
        assert change.kind is CHANGED
        assert change.known_artwork is known and change.observation is o

    def test_removed(self):
        known = art("a")
        (change,) = diff_reference_observations("s1", [known], [])
        assert change.kind is REMOVED
        assert change.known_artwork is known and change.observation is None

    def test_all_removed(self):
        result = diff_reference_observations("s1", [art("a"), art("b")], [])
        assert summary(result) == [(REMOVED, "a"), (REMOVED, "b")]

    def test_mixed_and_ordering(self):
        known = [art("r2"), art("u"), art("c"), art("r1")]
        observed = [obs("z"), obs("c", "h2"), obs("a"), obs("u")]
        result = diff_reference_observations("s1", known, observed)
        assert summary(result) == [
            (ADDED, "z"),
            (CHANGED, "c"),
            (ADDED, "a"),
            (UNCHANGED, "u"),
            (REMOVED, "r2"),
            (REMOVED, "r1"),
        ]

    def test_unrelated_sources_ignored(self):
        known = [art("a", source="s2"), art("b")]
        observed = [obs("a", source="s2"), obs("b")]
        assert summary(diff_reference_observations("s1", known, observed)) == [(UNCHANGED, "b")]
        assert summary(diff_reference_observations("s1", known, [obs("a", source="s2")])) == [
            (REMOVED, "b")
        ]
        assert summary(diff_reference_observations("s1", [art("b")], observed)) == [
            (UNCHANGED, "b")
        ]

    def test_duplicate_known_rejected(self):
        known = [art("a", art_id="x"), art("a", art_id="y")]
        with pytest.raises(ValueError) as exc:
            diff_reference_observations("s1", known, [])
        assert str(exc.value) == "Duplicate known artwork for source item ID: a."

    def test_duplicate_observations_rejected(self):
        with pytest.raises(ValueError) as exc:
            diff_reference_observations("s1", [], [obs("a"), obs("a", "h2")])
        assert str(exc.value) == "Duplicate observation for source item ID: a."

    def test_unrelated_duplicates_ignored(self):
        known = [art("a", source="s2", art_id="x"), art("a", source="s2", art_id="y"), art("b")]
        observed = [obs("a", source="s2"), obs("a", "h2", source="s2"), obs("b")]
        assert summary(diff_reference_observations("s1", known, observed)) == [(UNCHANGED, "b")]

    def test_same_hash_different_item_does_not_match(self):
        result = diff_reference_observations("s1", [art("old", "same")], [obs("new", "same")])
        assert summary(result) == [(ADDED, "new"), (REMOVED, "old")]

    def test_inputs_not_mutated(self):
        known = [art("a"), art("b")]
        observed = [obs("a", "h2"), obs("c")]
        known_copy, observed_copy = list(known), list(observed)

        def snap():
            return [(k.id, k.source_id, k.source_item_id, k.content_hash) for k in known]

        before = snap()
        diff_reference_observations("s1", known, observed)
        assert known == known_copy and observed == observed_copy
        assert snap() == before
