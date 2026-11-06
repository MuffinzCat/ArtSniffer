"""Tests for provider-neutral safety subject and clearance identities."""

from dataclasses import FrozenInstanceError
from typing import cast

import pytest

from artsniffer.safety.decision import SafetyGateDecision, SafetyGateReason
from artsniffer.safety.subject import SafetyClearedSubject, SafetySubject


def _subject() -> SafetySubject:
    return SafetySubject(artwork_id="artwork:one", content_hash="opaque:hash-v1")


@pytest.mark.parametrize(
    ("artwork_id", "content_hash"),
    [
        (" artwork:one ", " hash:v1 "),
        ("artwork:one", "sha256:0123456789abcdef"),
    ],
)
def test_safety_subject_preserves_supplied_identity_values(
    artwork_id: str, content_hash: str
) -> None:
    subject = SafetySubject(artwork_id=artwork_id, content_hash=content_hash)

    assert subject.artwork_id == artwork_id
    assert subject.content_hash == content_hash


@pytest.mark.parametrize("value", ["", " ", "\t\n", None, 42])
def test_safety_subject_rejects_invalid_artwork_id(value: object) -> None:
    with pytest.raises(ValueError) as error:
        SafetySubject(artwork_id=cast(str, value), content_hash="hash:v1")

    assert str(error.value) == "Safety subject artwork ID must not be empty or whitespace."


@pytest.mark.parametrize("value", ["", " ", "\t\n", None, 42])
def test_safety_subject_rejects_invalid_content_hash(value: object) -> None:
    with pytest.raises(ValueError) as error:
        SafetySubject(artwork_id="artwork:one", content_hash=cast(str, value))

    assert str(error.value) == "Safety subject content hash must not be empty or whitespace."


def test_artwork_id_and_content_hash_both_participate_in_identity() -> None:
    original = _subject()

    assert original != SafetySubject("artwork:one", "opaque:hash-v2")
    assert original != SafetySubject("artwork:two", "opaque:hash-v1")


def test_safety_subject_is_immutable() -> None:
    subject = _subject()

    with pytest.raises(FrozenInstanceError):
        subject.artwork_id = "artwork:two"  # type: ignore[misc]


def test_safety_cleared_subject_requires_cleared_decision() -> None:
    decision = SafetyGateDecision(True, SafetyGateReason.CLEARED)

    cleared = SafetyClearedSubject(_subject(), "criteria:complete:v1", decision)

    assert cleared.subject == _subject()
    assert cleared.criteria_id == "criteria:complete:v1"
    assert cleared.decision is decision


def test_safety_cleared_subject_rejects_non_safety_subject() -> None:
    with pytest.raises(ValueError) as error:
        SafetyClearedSubject(
            "artwork:one",  # type: ignore[arg-type]
            "criteria:complete:v1",
            SafetyGateDecision(True, SafetyGateReason.CLEARED),
        )

    assert str(error.value) == "Safety-cleared subject identity must be a SafetySubject."


@pytest.mark.parametrize("criteria_id", ["", " ", "\t\n", None, 42])
def test_safety_cleared_subject_rejects_invalid_criteria_id(criteria_id: object) -> None:
    with pytest.raises(ValueError) as error:
        SafetyClearedSubject(
            _subject(),
            criteria_id,  # type: ignore[arg-type]
            SafetyGateDecision(True, SafetyGateReason.CLEARED),
        )

    assert str(error.value) == (
        "Safety-cleared subject criteria ID must not be empty or whitespace."
    )


def test_safety_cleared_subject_rejects_non_safety_gate_decision() -> None:
    with pytest.raises(ValueError) as error:
        SafetyClearedSubject(
            _subject(),
            "criteria:complete:v1",
            "cleared",  # type: ignore[arg-type]
        )

    assert str(error.value) == "Safety-cleared subject requires a CLEARED safety gate decision."


def test_safety_cleared_subject_is_immutable() -> None:
    cleared = SafetyClearedSubject(
        _subject(),
        "criteria:complete:v1",
        SafetyGateDecision(True, SafetyGateReason.CLEARED),
    )

    with pytest.raises(FrozenInstanceError):
        cleared.criteria_id = "criteria:complete:v2"  # type: ignore[misc]


@pytest.mark.parametrize(
    "decision",
    [
        SafetyGateDecision(False, SafetyGateReason.PROHIBITED),
        SafetyGateDecision(False, SafetyGateReason.INSUFFICIENT_METADATA),
    ],
)
def test_safety_cleared_subject_rejects_non_cleared_decisions(
    decision: SafetyGateDecision,
) -> None:
    with pytest.raises(ValueError) as error:
        SafetyClearedSubject(_subject(), "criteria:complete:v1", decision)

    assert str(error.value) == "Safety-cleared subject requires a CLEARED safety gate decision."
