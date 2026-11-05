"""Tests for the unconditional safety gate decision vocabulary."""

import ast
from pathlib import Path

import pytest

from artsniffer.safety.decision import SafetyGateDecision, SafetyGateReason


def test_safety_gate_reason_values_are_exact() -> None:
    """Verify the exact string values of SafetyGateReason members."""
    assert {reason.name: reason.value for reason in SafetyGateReason} == {
        "CLEARED": "cleared",
        "PROHIBITED": "prohibited",
        "INSUFFICIENT_METADATA": "insufficient_metadata",
    }


def test_safety_gate_reason_has_exactly_three_members() -> None:
    """Verify SafetyGateReason has exactly three members."""
    assert len(SafetyGateReason) == 3


def test_safety_gate_reason_is_str_enum() -> None:
    """Verify SafetyGateReason is a StrEnum."""
    assert isinstance(SafetyGateReason.CLEARED, str)
    assert isinstance(SafetyGateReason.PROHIBITED, str)
    assert isinstance(SafetyGateReason.INSUFFICIENT_METADATA, str)


@pytest.mark.parametrize(
    ("cleared", "reason"),
    [
        (True, SafetyGateReason.CLEARED),
        (False, SafetyGateReason.PROHIBITED),
        (False, SafetyGateReason.INSUFFICIENT_METADATA),
    ],
)
def test_valid_safety_gate_decision_combinations(cleared: bool, reason: SafetyGateReason) -> None:
    """Verify valid SafetyGateDecision combinations can be created."""
    decision = SafetyGateDecision(cleared=cleared, reason=reason)
    assert decision.cleared is cleared
    assert decision.reason is reason


@pytest.mark.parametrize(
    ("cleared", "reason"),
    [
        (False, SafetyGateReason.CLEARED),
        (True, SafetyGateReason.PROHIBITED),
        (True, SafetyGateReason.INSUFFICIENT_METADATA),
    ],
)
def test_invalid_safety_gate_decision_combinations_raise_value_error(
    cleared: bool, reason: SafetyGateReason
) -> None:
    """Verify invalid SafetyGateDecision combinations raise ValueError."""
    with pytest.raises(ValueError) as error:
        SafetyGateDecision(cleared=cleared, reason=reason)

    assert str(error.value) == "Safety gate cleared flag must agree with the decision reason."


def test_safety_gate_decision_is_immutable() -> None:
    """Verify SafetyGateDecision is immutable (frozen)."""
    decision = SafetyGateDecision(cleared=True, reason=SafetyGateReason.CLEARED)

    with pytest.raises(AttributeError):
        decision.cleared = False  # type: ignore

    with pytest.raises(AttributeError):
        decision.reason = SafetyGateReason.PROHIBITED  # type: ignore


def test_safety_gate_decision_has_exactly_two_fields() -> None:
    """Verify SafetyGateDecision has exactly two fields and no extras."""
    decision = SafetyGateDecision(cleared=True, reason=SafetyGateReason.CLEARED)

    field_names = {field.name for field in decision.__dataclass_fields__.values()}
    assert field_names == {"cleared", "reason"}
    assert len(decision.__dataclass_fields__) == 2


def test_safety_module_imports_no_artsniffer_domain_package() -> None:
    """Verify the safety decision module depends only on Python standard library."""
    decision_path = (
        Path(__file__).resolve().parents[2] / "src/artsniffer/safety/decision.py"
    )
    decision_ast = ast.parse(decision_path.read_text(encoding="utf-8"))
    imported_modules = [
        alias.name
        for node in ast.walk(decision_ast)
        if isinstance(node, ast.Import)
        for alias in node.names
    ] + [
        node.module
        for node in ast.walk(decision_ast)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    ]

    artsniffer_imports = [
        module
        for module in imported_modules
        if module == "artsniffer" or module.startswith("artsniffer.")
    ]
    assert not artsniffer_imports, (
        f"Found artsniffer imports in safety.decision: {artsniffer_imports}"
    )
