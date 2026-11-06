"""Tests for provider-neutral unconditional safety evidence claims."""

import ast
import sys
from dataclasses import FrozenInstanceError, replace
from enum import StrEnum
from pathlib import Path

import pytest

from artsniffer.content.rating import ContentRating
from artsniffer.discovery.content_rating import DiscoveredArtworkContentRating
from artsniffer.safety.evidence import (
    SafetyEvidence,
    SafetyEvidenceAssertion,
    SafetyEvidenceMethod,
    SafetyEvidenceOrigin,
)


def _evidence() -> SafetyEvidence:
    return SafetyEvidence(
        assertion=SafetyEvidenceAssertion.SUPPORTS_CLEARANCE,
        origin=SafetyEvidenceOrigin.SOURCE_METADATA,
        producer_id=" source:producer ",
        criteria_id=" criteria:complete:v1 ",
        method=SafetyEvidenceMethod.UNKNOWN,
    )


def _model_evidence(confidence: float | None = None) -> SafetyEvidence:
    return replace(
        _evidence(),
        origin=SafetyEvidenceOrigin.SAFETY_ANALYSIS,
        method=SafetyEvidenceMethod.MODEL,
        model_id="model:example",
        model_version="v1",
        confidence=confidence,
    )


def test_enum_vocabularies_are_exact() -> None:
    assert {member.name: member.value for member in SafetyEvidenceAssertion} == {
        "SUPPORTS_CLEARANCE": "supports_clearance",
        "INDICATES_PROHIBITED": "indicates_prohibited",
        "INSUFFICIENT": "insufficient",
    }
    assert {member.name: member.value for member in SafetyEvidenceOrigin} == {
        "SOURCE_METADATA": "source_metadata",
        "SAFETY_ANALYSIS": "safety_analysis",
        "OTHER_MODERATION": "other_moderation",
    }
    assert {member.name: member.value for member in SafetyEvidenceMethod} == {
        "MODEL": "model",
        "NON_MODEL": "non_model",
        "UNKNOWN": "unknown",
    }


@pytest.mark.parametrize("assertion", list(SafetyEvidenceAssertion))
@pytest.mark.parametrize("origin", list(SafetyEvidenceOrigin))
@pytest.mark.parametrize("method", [SafetyEvidenceMethod.NON_MODEL, SafetyEvidenceMethod.UNKNOWN])
def test_non_model_claims_preserve_fields(
    assertion: SafetyEvidenceAssertion,
    origin: SafetyEvidenceOrigin,
    method: SafetyEvidenceMethod,
) -> None:
    evidence = replace(_evidence(), assertion=assertion, origin=origin, method=method)

    assert evidence.assertion is assertion
    assert evidence.origin is origin
    assert evidence.method is method
    assert evidence.producer_id == " source:producer "
    assert evidence.criteria_id == " criteria:complete:v1 "
    assert evidence.model_id is None
    assert evidence.model_version is None
    assert evidence.confidence is None


@pytest.mark.parametrize("assertion", list(SafetyEvidenceAssertion))
@pytest.mark.parametrize("origin", list(SafetyEvidenceOrigin))
def test_model_claims_preserve_provenance(
    assertion: SafetyEvidenceAssertion, origin: SafetyEvidenceOrigin
) -> None:
    evidence = replace(_model_evidence(0.75), assertion=assertion, origin=origin)

    assert evidence.assertion is assertion
    assert evidence.origin is origin
    assert evidence.method is SafetyEvidenceMethod.MODEL
    assert evidence.model_id == "model:example"
    assert evidence.model_version == "v1"
    assert evidence.confidence == 0.75


def test_evidence_is_immutable() -> None:
    evidence = _evidence()
    with pytest.raises(FrozenInstanceError):
        evidence.criteria_id = "different"  # type: ignore[misc]


class _OtherAssertion(StrEnum):
    SUPPORTS_CLEARANCE = "supports_clearance"


@pytest.mark.parametrize(
    "assertion",
    [
        "supports_clearance",
        "unrecognised",
        _OtherAssertion.SUPPORTS_CLEARANCE,
        ContentRating.UNKNOWN,
        DiscoveredArtworkContentRating("artwork", "source", ContentRating.GENERAL),
        ("source-tag",),
        None,
    ],
)
def test_rejects_non_assertions(assertion: SafetyEvidenceAssertion) -> None:
    with pytest.raises(ValueError) as error:
        replace(_evidence(), assertion=assertion)
    assert str(error.value) == "Safety evidence assertion must be a SafetyEvidenceAssertion."


@pytest.mark.parametrize("origin", ["source_metadata", "invalid", SafetyEvidenceMethod.MODEL, None])
def test_rejects_invalid_origin(origin: SafetyEvidenceOrigin) -> None:
    with pytest.raises(ValueError) as error:
        replace(_evidence(), origin=origin)
    assert str(error.value) == "Safety evidence origin must be a SafetyEvidenceOrigin."


@pytest.mark.parametrize(
    "method", ["unknown", "invalid", SafetyEvidenceOrigin.SOURCE_METADATA, None]
)
def test_rejects_invalid_method(method: SafetyEvidenceMethod) -> None:
    with pytest.raises(ValueError) as error:
        replace(_evidence(), method=method)
    assert str(error.value) == "Safety evidence method must be a SafetyEvidenceMethod."


@pytest.mark.parametrize("identifier", ["", " ", "\t\n", None, 42])
def test_rejects_invalid_producer_id(identifier: str) -> None:
    with pytest.raises(ValueError) as error:
        replace(_evidence(), producer_id=identifier)
    assert str(error.value) == "Safety evidence producer ID must not be empty or whitespace."


@pytest.mark.parametrize("identifier", ["", " ", "\t\n", None, 42])
def test_rejects_invalid_criteria_id(identifier: str) -> None:
    with pytest.raises(ValueError) as error:
        replace(_evidence(), criteria_id=identifier)
    assert str(error.value) == "Safety evidence criteria ID must not be empty or whitespace."


@pytest.mark.parametrize("identifier", [None, "", " \t", 42])
def test_model_requires_valid_model_id(identifier: str | None) -> None:
    with pytest.raises(ValueError) as error:
        replace(_model_evidence(), model_id=identifier)
    assert str(error.value) == "Model evidence requires a non-empty model ID."


@pytest.mark.parametrize("version", [None, "", " \t", 42])
def test_model_requires_valid_model_version(version: str | None) -> None:
    with pytest.raises(ValueError) as error:
        replace(_model_evidence(), model_version=version)
    assert str(error.value) == "Model evidence requires a non-empty model version."


@pytest.mark.parametrize("method", [SafetyEvidenceMethod.NON_MODEL, SafetyEvidenceMethod.UNKNOWN])
def test_non_model_methods_reject_model_id(method: SafetyEvidenceMethod) -> None:
    with pytest.raises(ValueError) as error:
        replace(_evidence(), method=method, model_id="model")
    assert str(error.value) == "Model ID must be absent for non-model or unknown methods."


@pytest.mark.parametrize("method", [SafetyEvidenceMethod.NON_MODEL, SafetyEvidenceMethod.UNKNOWN])
def test_non_model_methods_reject_model_version(method: SafetyEvidenceMethod) -> None:
    with pytest.raises(ValueError) as error:
        replace(_evidence(), method=method, model_version="version")
    assert str(error.value) == "Model version must be absent for non-model or unknown methods."


@pytest.mark.parametrize("method", [SafetyEvidenceMethod.NON_MODEL, SafetyEvidenceMethod.UNKNOWN])
def test_non_model_methods_reject_confidence(method: SafetyEvidenceMethod) -> None:
    with pytest.raises(ValueError) as error:
        replace(_evidence(), method=method, confidence=0.5)
    assert str(error.value) == "Confidence must be absent for non-model or unknown methods."


@pytest.mark.parametrize("confidence", [None, 0.0, 0.25, 1.0, 0, 1])
def test_model_accepts_optional_confidence(confidence: float | None) -> None:
    assert _model_evidence(confidence).confidence == confidence


@pytest.mark.parametrize(
    "confidence",
    [-0.01, 1.01, float("nan"), float("inf"), float("-inf"), True, False, "0.5", [], 10**400],
)
def test_model_rejects_invalid_confidence(confidence: float) -> None:
    with pytest.raises(ValueError) as error:
        _model_evidence(confidence)
    assert str(error.value) == "Safety evidence confidence must be finite and between 0 and 1."


def test_absence_is_distinct_from_explicit_insufficient_evidence() -> None:
    absent: tuple[SafetyEvidence, ...] = ()
    insufficient = replace(_evidence(), assertion=SafetyEvidenceAssertion.INSUFFICIENT)

    assert not absent
    assert (insufficient,) != absent
    assert insufficient.producer_id == " source:producer "
    assert insufficient.criteria_id == " criteria:complete:v1 "


def test_evidence_module_imports_only_standard_library_modules() -> None:
    evidence_path = Path(__file__).resolve().parents[2] / "src/artsniffer/safety/evidence.py"
    evidence_ast = ast.parse(evidence_path.read_text(encoding="utf-8"))
    imports = [
        node for node in ast.walk(evidence_ast) if isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    relative_imports = [
        node for node in imports if isinstance(node, ast.ImportFrom) and node.level > 0
    ]
    modules = [
        alias.name for node in imports if isinstance(node, ast.Import) for alias in node.names
    ] + [
        node.module
        for node in imports
        if isinstance(node, ast.ImportFrom) and node.module is not None
    ]
    non_standard = {module.partition(".")[0] for module in modules} - sys.stdlib_module_names

    assert not relative_imports
    assert not non_standard
