"""Tests for subject-bound safety evidence evaluation."""

import ast
import sys
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from typing import cast

import pytest

from artsniffer.safety.authority import SafetyEvidenceAuthority
from artsniffer.safety.binding import (
    BoundSafetyEvidence,
    SafetyEvaluationResult,
    evaluate_bound_safety_evidence,
)
from artsniffer.safety.decision import SafetyGateDecision, SafetyGateReason
from artsniffer.safety.evidence import (
    SafetyEvidence,
    SafetyEvidenceAssertion,
    SafetyEvidenceMethod,
    SafetyEvidenceOrigin,
)
from artsniffer.safety.subject import SafetyClearedSubject, SafetySubject

_CRITERIA_ID = "criteria:complete:v1"


def _subject(
    artwork_id: str = "artwork:one",
    content_hash: str = "opaque:hash-v1",
) -> SafetySubject:
    return SafetySubject(artwork_id, content_hash)


def _evidence(
    assertion: SafetyEvidenceAssertion = SafetyEvidenceAssertion.SUPPORTS_CLEARANCE,
    criteria_id: str = _CRITERIA_ID,
) -> SafetyEvidence:
    return SafetyEvidence(
        assertion=assertion,
        origin=SafetyEvidenceOrigin.SOURCE_METADATA,
        producer_id="producer:example",
        criteria_id=criteria_id,
        method=SafetyEvidenceMethod.NON_MODEL,
    )


def _bound(
    subject: SafetySubject | None = None,
    claim: SafetyEvidence | None = None,
) -> BoundSafetyEvidence:
    return BoundSafetyEvidence(subject or _subject(), claim or _evidence())


def _authority(
    criteria_id: str = _CRITERIA_ID,
) -> SafetyEvidenceAuthority:
    return SafetyEvidenceAuthority(
        producer_id="producer:example",
        criteria_id=criteria_id,
        origin=SafetyEvidenceOrigin.SOURCE_METADATA,
        method=SafetyEvidenceMethod.NON_MODEL,
        allowed_assertions=frozenset(SafetyEvidenceAssertion),
    )


def test_bound_clearance_returns_subject_and_criteria_bound_token() -> None:
    subject = _subject()

    result = evaluate_bound_safety_evidence(
        subject,
        (_bound(subject),),
        _CRITERIA_ID,
        (_authority(),),
    )

    assert result == SafetyEvaluationResult(
        subject,
        _CRITERIA_ID,
        SafetyGateDecision(True, SafetyGateReason.CLEARED),
    )
    assert result.cleared_subject == SafetyClearedSubject(
        subject,
        _CRITERIA_ID,
        SafetyGateDecision(True, SafetyGateReason.CLEARED),
    )


def test_bound_safety_evidence_rejects_non_safety_subject() -> None:
    with pytest.raises(ValueError) as error:
        BoundSafetyEvidence(
            "artwork:one",  # type: ignore[arg-type]
            _evidence(),
        )

    assert str(error.value) == "Bound safety evidence subject must be a SafetySubject."


@pytest.mark.parametrize(
    ("claims", "authorities", "reason"),
    [
        ((), (_authority(),), SafetyGateReason.INSUFFICIENT_METADATA),
        (
            (_bound(claim=_evidence(SafetyEvidenceAssertion.INSUFFICIENT)),),
            (_authority(),),
            SafetyGateReason.INSUFFICIENT_METADATA,
        ),
        ((_bound(),), (), SafetyGateReason.INSUFFICIENT_METADATA),
        (
            (_bound(claim=_evidence(criteria_id="criteria:complete:v2")),),
            (_authority("criteria:complete:v2"),),
            SafetyGateReason.INSUFFICIENT_METADATA,
        ),
        (
            (_bound(claim=_evidence(SafetyEvidenceAssertion.INDICATES_PROHIBITED)),),
            (_authority(),),
            SafetyGateReason.PROHIBITED,
        ),
        (
            (
                _bound(),
                _bound(claim=_evidence(SafetyEvidenceAssertion.INDICATES_PROHIBITED)),
            ),
            (_authority(),),
            SafetyGateReason.PROHIBITED,
        ),
    ],
)
def test_non_cleared_evaluation_preserves_decision_without_token(
    claims: tuple[BoundSafetyEvidence, ...],
    authorities: tuple[SafetyEvidenceAuthority, ...],
    reason: SafetyGateReason,
) -> None:
    result = evaluate_bound_safety_evidence(_subject(), claims, _CRITERIA_ID, authorities)

    assert result.subject == _subject()
    assert result.criteria_id == _CRITERIA_ID
    assert result.decision == SafetyGateDecision(
        reason is SafetyGateReason.CLEARED,
        reason,
    )
    assert result.cleared_subject is None


@pytest.mark.parametrize(
    "mismatched_subject",
    [
        SafetySubject("artwork:other", "opaque:hash-v2"),
        SafetySubject("artwork:one", "opaque:hash-v2"),
        SafetySubject("artwork:other", "opaque:hash-v1"),
    ],
)
def test_mismatched_subject_evidence_fails_closed(
    mismatched_subject: SafetySubject,
) -> None:
    with pytest.raises(ValueError) as error:
        evaluate_bound_safety_evidence(
            _subject(),
            (_bound(mismatched_subject),),
            _CRITERIA_ID,
            (_authority(),),
        )

    assert str(error.value) == "All bound safety evidence must match the requested subject."


def test_mixed_subject_evidence_fails_closed() -> None:
    with pytest.raises(ValueError) as error:
        evaluate_bound_safety_evidence(
            _subject(),
            (_bound(), _bound(SafetySubject("artwork:one", "opaque:hash-v2"))),
            _CRITERIA_ID,
            (_authority(),),
        )

    assert str(error.value) == "All bound safety evidence must match the requested subject."


def test_duplicate_bound_evidence_fails_closed() -> None:
    bound = _bound()

    with pytest.raises(ValueError) as error:
        evaluate_bound_safety_evidence(
            _subject(),
            (bound, bound),
            _CRITERIA_ID,
            (_authority(),),
        )

    assert str(error.value) == "Bound safety evidence must not contain duplicates."


def test_criteria_versions_remain_bound_to_results_and_tokens() -> None:
    result = evaluate_bound_safety_evidence(
        _subject(),
        (_bound(claim=_evidence(criteria_id="criteria:complete:v2")),),
        "criteria:complete:v2",
        (_authority("criteria:complete:v2"),),
    )

    assert result.cleared_subject is not None
    assert result.cleared_subject.criteria_id == "criteria:complete:v2"
    assert result.cleared_subject.criteria_id != _CRITERIA_ID

    other_version = evaluate_bound_safety_evidence(
        _subject(),
        (_bound(claim=_evidence(criteria_id="criteria:complete:v1")),),
        "criteria:complete:v2",
        (_authority("criteria:complete:v1"),),
    )

    assert other_version.criteria_id == "criteria:complete:v2"
    assert other_version.decision.reason is SafetyGateReason.INSUFFICIENT_METADATA
    assert other_version.cleared_subject is None


def test_binding_evaluation_does_not_mutate_inputs() -> None:
    bound = _bound()
    authority = _authority()
    claims_before = replace(bound.evidence)
    authority_before = replace(authority)

    evaluate_bound_safety_evidence(_subject(), (bound,), _CRITERIA_ID, (authority,))

    assert bound.evidence == claims_before
    assert authority == authority_before


def test_rejects_malformed_binding_items() -> None:
    with pytest.raises(ValueError) as error:
        evaluate_bound_safety_evidence(
            _subject(),
            (replace(_bound(), evidence=object()),),  # type: ignore[arg-type]
            _CRITERIA_ID,
            (_authority(),),
        )

    assert str(error.value) == "Bound safety evidence claim must be a SafetyEvidence."


def test_safety_evaluation_result_rejects_non_safety_subject() -> None:
    with pytest.raises(ValueError) as error:
        SafetyEvaluationResult(
            "artwork:one",  # type: ignore[arg-type]
            _CRITERIA_ID,
            SafetyGateDecision(False, SafetyGateReason.INSUFFICIENT_METADATA),
        )

    assert str(error.value) == "Safety evaluation subject must be a SafetySubject."


@pytest.mark.parametrize("criteria_id", ["", " ", "\t\n", None, 42])
def test_safety_evaluation_result_rejects_invalid_criteria_id(criteria_id: object) -> None:
    with pytest.raises(ValueError) as error:
        SafetyEvaluationResult(
            _subject(),
            cast(str, criteria_id),
            SafetyGateDecision(False, SafetyGateReason.INSUFFICIENT_METADATA),
        )

    assert str(error.value) == "Safety evaluation criteria ID must not be empty or whitespace."


def test_safety_evaluation_result_rejects_non_safety_gate_decision() -> None:
    with pytest.raises(ValueError) as error:
        SafetyEvaluationResult(
            _subject(),
            _CRITERIA_ID,
            "insufficient",  # type: ignore[arg-type]
        )

    assert str(error.value) == "Safety evaluation decision must be a SafetyGateDecision."


def test_safety_evaluation_result_is_immutable() -> None:
    result = SafetyEvaluationResult(
        _subject(),
        _CRITERIA_ID,
        SafetyGateDecision(False, SafetyGateReason.INSUFFICIENT_METADATA),
    )

    with pytest.raises(FrozenInstanceError):
        result.criteria_id = "criteria:complete:v2"  # type: ignore[misc]


@pytest.mark.parametrize("module_name", ["subject", "binding"])
def test_safety_binding_modules_import_only_standard_library_and_safety(
    module_name: str,
) -> None:
    module_path = (
        Path(__file__).resolve().parents[2] / "src" / "artsniffer" / "safety" / f"{module_name}.py"
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    allowed_safety_modules = {
        "artsniffer.safety.authority",
        "artsniffer.safety.binding",
        "artsniffer.safety.decision",
        "artsniffer.safety.evaluation",
        "artsniffer.safety.evidence",
        "artsniffer.safety.subject",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            assert node.module is not None
            modules = [node.module]
        else:
            continue
        for module in modules:
            assert (
                module.partition(".")[0] in sys.stdlib_module_names
                or module in allowed_safety_modules
            ), f"Unexpected dependency: {module}"
