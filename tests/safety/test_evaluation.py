"""Tests for pure, fail-closed evaluation of independently authorised safety claims."""

import ast
import sys
from dataclasses import replace
from itertools import permutations
from pathlib import Path

import pytest

from artsniffer.safety.authority import SafetyEvidenceAuthority
from artsniffer.safety.decision import SafetyGateDecision, SafetyGateReason
from artsniffer.safety.evaluation import evaluate_safety_evidence
from artsniffer.safety.evidence import (
    SafetyEvidence,
    SafetyEvidenceAssertion,
    SafetyEvidenceMethod,
    SafetyEvidenceOrigin,
)


def _authority() -> SafetyEvidenceAuthority:
    return SafetyEvidenceAuthority(
        producer_id="producer:example",
        criteria_id="criteria:complete:v1",
        origin=SafetyEvidenceOrigin.SOURCE_METADATA,
        method=SafetyEvidenceMethod.NON_MODEL,
        allowed_assertions=frozenset(SafetyEvidenceAssertion),
    )


def _evidence(
    assertion: SafetyEvidenceAssertion = SafetyEvidenceAssertion.SUPPORTS_CLEARANCE,
) -> SafetyEvidence:
    return SafetyEvidence(
        assertion=assertion,
        producer_id="producer:example",
        criteria_id="criteria:complete:v1",
        origin=SafetyEvidenceOrigin.SOURCE_METADATA,
        method=SafetyEvidenceMethod.NON_MODEL,
    )


def _model_authority() -> SafetyEvidenceAuthority:
    return replace(
        _authority(),
        method=SafetyEvidenceMethod.MODEL,
        model_id="model:example",
        model_version="v1",
    )


def _model_evidence() -> SafetyEvidence:
    return replace(
        _evidence(),
        method=SafetyEvidenceMethod.MODEL,
        model_id="model:example",
        model_version="v1",
    )


@pytest.mark.parametrize(
    ("assertions", "reason"),
    [
        ((), SafetyGateReason.INSUFFICIENT_METADATA),
        ((SafetyEvidenceAssertion.INSUFFICIENT,), SafetyGateReason.INSUFFICIENT_METADATA),
        (
            (SafetyEvidenceAssertion.INSUFFICIENT, SafetyEvidenceAssertion.INSUFFICIENT),
            SafetyGateReason.INSUFFICIENT_METADATA,
        ),
        ((SafetyEvidenceAssertion.SUPPORTS_CLEARANCE,), SafetyGateReason.CLEARED),
        (
            (
                SafetyEvidenceAssertion.SUPPORTS_CLEARANCE,
                SafetyEvidenceAssertion.SUPPORTS_CLEARANCE,
            ),
            SafetyGateReason.CLEARED,
        ),
        ((SafetyEvidenceAssertion.INDICATES_PROHIBITED,), SafetyGateReason.PROHIBITED),
        (
            (SafetyEvidenceAssertion.SUPPORTS_CLEARANCE, SafetyEvidenceAssertion.INSUFFICIENT),
            SafetyGateReason.CLEARED,
        ),
        (
            (
                SafetyEvidenceAssertion.SUPPORTS_CLEARANCE,
                SafetyEvidenceAssertion.INDICATES_PROHIBITED,
            ),
            SafetyGateReason.PROHIBITED,
        ),
        (
            (SafetyEvidenceAssertion.INSUFFICIENT, SafetyEvidenceAssertion.INDICATES_PROHIBITED),
            SafetyGateReason.PROHIBITED,
        ),
        (tuple(SafetyEvidenceAssertion), SafetyGateReason.PROHIBITED),
    ],
)
def test_decision_truth_table(
    assertions: tuple[SafetyEvidenceAssertion, ...], reason: SafetyGateReason
) -> None:
    evidence = tuple(_evidence(assertion) for assertion in assertions)
    assert evaluate_safety_evidence(evidence, "criteria:complete:v1", (_authority(),)) == (
        SafetyGateDecision(reason is SafetyGateReason.CLEARED, reason)
    )


@pytest.mark.parametrize("assertion", list(SafetyEvidenceAssertion))
def test_no_authorities_never_clears(assertion: SafetyEvidenceAssertion) -> None:
    assert evaluate_safety_evidence((_evidence(assertion),), "criteria:complete:v1", ()) == (
        SafetyGateDecision(False, SafetyGateReason.INSUFFICIENT_METADATA)
    )


@pytest.mark.parametrize(
    ("claim", "grant"),
    [
        (replace(_evidence(), producer_id="other"), _authority()),
        (_evidence(), replace(_authority(), producer_id="other")),
        (_evidence(), replace(_authority(), criteria_id="criteria:complete:v2")),
        (
            _evidence(),
            replace(_authority(), origin=SafetyEvidenceOrigin.SAFETY_ANALYSIS),
        ),
        (
            _evidence(),
            replace(_authority(), origin=SafetyEvidenceOrigin.OTHER_MODERATION),
        ),
        (_evidence(), replace(_authority(), method=SafetyEvidenceMethod.UNKNOWN)),
        (replace(_evidence(), method=SafetyEvidenceMethod.UNKNOWN), _authority()),
        (_model_evidence(), _authority()),
        (_evidence(), _model_authority()),
        (_model_evidence(), replace(_authority(), method=SafetyEvidenceMethod.UNKNOWN)),
        (_model_evidence(), replace(_model_authority(), model_id="model:other")),
        (_model_evidence(), replace(_model_authority(), model_version="v2")),
        (
            _evidence(),
            replace(
                _authority(),
                allowed_assertions=frozenset({SafetyEvidenceAssertion.INDICATES_PROHIBITED}),
            ),
        ),
        (replace(_evidence(), producer_id=" producer:example "), _authority()),
        (
            replace(_model_evidence(), model_version=" v1 "),
            _model_authority(),
        ),
    ],
)
@pytest.mark.parametrize("assertion", list(SafetyEvidenceAssertion))
def test_unauthorised_claims_are_ignored(
    claim: SafetyEvidence, grant: SafetyEvidenceAuthority, assertion: SafetyEvidenceAssertion
) -> None:
    # Keep the assertion-permission case unauthorised even when changing the claim's assertion.
    if grant.allowed_assertions != frozenset(SafetyEvidenceAssertion):
        grant = replace(
            grant,
            allowed_assertions=frozenset(
                candidate for candidate in SafetyEvidenceAssertion if candidate is not assertion
            ),
        )
    claim = replace(claim, assertion=assertion)
    assert evaluate_safety_evidence((claim,), "criteria:complete:v1", (grant,)) == (
        SafetyGateDecision(False, SafetyGateReason.INSUFFICIENT_METADATA)
    )
    clearance = replace(_evidence(), producer_id="producer:independent-clearance")
    clearance_grant = replace(_authority(), producer_id=clearance.producer_id)
    assert evaluate_safety_evidence(
        (claim, clearance), "criteria:complete:v1", (grant, clearance_grant)
    ) == SafetyGateDecision(True, SafetyGateReason.CLEARED)


@pytest.mark.parametrize("assertion", list(SafetyEvidenceAssertion))
def test_other_criteria_are_ignored_even_with_matching_grant(
    assertion: SafetyEvidenceAssertion,
) -> None:
    claim = replace(_evidence(assertion), criteria_id="criteria:complete:v2")
    grant = replace(_authority(), criteria_id=claim.criteria_id)
    assert evaluate_safety_evidence((claim,), "criteria:complete:v1", (grant,)) == (
        SafetyGateDecision(False, SafetyGateReason.INSUFFICIENT_METADATA)
    )
    assert evaluate_safety_evidence(
        (claim, _evidence()), "criteria:complete:v1", (grant, _authority())
    ) == SafetyGateDecision(True, SafetyGateReason.CLEARED)


@pytest.mark.parametrize("assertion", list(SafetyEvidenceAssertion))
@pytest.mark.parametrize("method", list(SafetyEvidenceMethod))
@pytest.mark.parametrize("origin", list(SafetyEvidenceOrigin))
def test_exact_authority_can_permit_each_channel_method_and_assertion(
    assertion: SafetyEvidenceAssertion,
    method: SafetyEvidenceMethod,
    origin: SafetyEvidenceOrigin,
) -> None:
    claim = _model_evidence() if method is SafetyEvidenceMethod.MODEL else _evidence()
    grant = _model_authority() if method is SafetyEvidenceMethod.MODEL else _authority()
    claim = replace(claim, assertion=assertion, method=method, origin=origin)
    grant = replace(grant, method=method, origin=origin, allowed_assertions=frozenset({assertion}))
    reason = {
        SafetyEvidenceAssertion.SUPPORTS_CLEARANCE: SafetyGateReason.CLEARED,
        SafetyEvidenceAssertion.INDICATES_PROHIBITED: SafetyGateReason.PROHIBITED,
        SafetyEvidenceAssertion.INSUFFICIENT: SafetyGateReason.INSUFFICIENT_METADATA,
    }[assertion]
    assert evaluate_safety_evidence((claim,), claim.criteria_id, (grant,)) == SafetyGateDecision(
        reason is SafetyGateReason.CLEARED, reason
    )


@pytest.mark.parametrize("confidence", [None, 0.0, 0.5, 1.0])
@pytest.mark.parametrize("assertion", list(SafetyEvidenceAssertion))
def test_confidence_has_no_effect(
    confidence: float | None, assertion: SafetyEvidenceAssertion
) -> None:
    claim = replace(_model_evidence(), assertion=assertion)
    for authorities in ((), (_model_authority(),)):
        assert evaluate_safety_evidence(
            (replace(claim, confidence=confidence),), claim.criteria_id, authorities
        ) == evaluate_safety_evidence((claim,), claim.criteria_id, authorities)


@pytest.mark.parametrize(
    ("assertions", "reason"),
    [
        (tuple(SafetyEvidenceAssertion), SafetyGateReason.PROHIBITED),
        (
            (SafetyEvidenceAssertion.SUPPORTS_CLEARANCE, SafetyEvidenceAssertion.INSUFFICIENT),
            SafetyGateReason.CLEARED,
        ),
        ((SafetyEvidenceAssertion.INSUFFICIENT,), SafetyGateReason.INSUFFICIENT_METADATA),
    ],
)
def test_order_duplicates_and_inputs_unchanged(
    assertions: tuple[SafetyEvidenceAssertion, ...], reason: SafetyGateReason
) -> None:
    claims = tuple(
        replace(_evidence(assertion), producer_id=f"producer:{index}")
        for index, assertion in enumerate(assertions)
    )
    grants = tuple(replace(_authority(), producer_id=claim.producer_id) for claim in claims)
    claims_before = tuple(replace(claim) for claim in claims)
    grants_before = tuple(replace(grant) for grant in grants)
    expected = SafetyGateDecision(reason is SafetyGateReason.CLEARED, reason)
    for claim_order in permutations(claims):
        for grant_order in permutations(grants):
            assert (
                evaluate_safety_evidence(claim_order, "criteria:complete:v1", grant_order)
                == expected
            )
            assert (
                evaluate_safety_evidence(claim_order * 2, "criteria:complete:v1", grant_order)
                == expected
            )
            assert (
                evaluate_safety_evidence(claim_order, "criteria:complete:v1", grant_order * 2)
                == expected
            )
            assert (
                evaluate_safety_evidence(claim_order * 2, "criteria:complete:v1", grant_order * 2)
                == expected
            )
    assert claims == claims_before
    assert grants == grants_before


@pytest.mark.parametrize("criteria_id", ["", " ", "\t\n", None, 42, False])
def test_invalid_requested_criteria_id(criteria_id: str) -> None:
    with pytest.raises(ValueError) as error:
        evaluate_safety_evidence((), criteria_id, ())
    assert str(error.value) == "Safety evaluation criteria ID must not be empty or whitespace."


@pytest.mark.parametrize("module_name", ["authority", "evaluation"])
def test_source_dependency_boundary(module_name: str) -> None:
    module_path = (
        Path(__file__).resolve().parents[2] / "src" / "artsniffer" / "safety" / f"{module_name}.py"
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    allowed_safety_modules = {
        "artsniffer.safety.authority",
        "artsniffer.safety.decision",
        "artsniffer.safety.evidence",
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
