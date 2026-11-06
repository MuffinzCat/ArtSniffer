"""Tests for independently configured safety-evidence authority grants."""

from dataclasses import FrozenInstanceError, fields, replace
from enum import StrEnum

import pytest

from artsniffer.safety.authority import SafetyEvidenceAuthority
from artsniffer.safety.evidence import (
    SafetyEvidenceAssertion,
    SafetyEvidenceMethod,
    SafetyEvidenceOrigin,
)


def _authority() -> SafetyEvidenceAuthority:
    return SafetyEvidenceAuthority(
        producer_id=" producer:example ",
        criteria_id=" criteria:complete:v1 ",
        origin=SafetyEvidenceOrigin.SOURCE_METADATA,
        method=SafetyEvidenceMethod.UNKNOWN,
        allowed_assertions=frozenset({SafetyEvidenceAssertion.SUPPORTS_CLEARANCE}),
    )


def _model_authority() -> SafetyEvidenceAuthority:
    return replace(
        _authority(),
        method=SafetyEvidenceMethod.MODEL,
        model_id="model:example",
        model_version="v1",
    )


@pytest.mark.parametrize("origin", list(SafetyEvidenceOrigin))
@pytest.mark.parametrize("method", list(SafetyEvidenceMethod))
@pytest.mark.parametrize("assertion", list(SafetyEvidenceAssertion))
def test_valid_grants_preserve_exact_scope(
    origin: SafetyEvidenceOrigin,
    method: SafetyEvidenceMethod,
    assertion: SafetyEvidenceAssertion,
) -> None:
    base = _model_authority() if method is SafetyEvidenceMethod.MODEL else _authority()
    grant = replace(base, origin=origin, method=method, allowed_assertions=frozenset({assertion}))

    assert grant.producer_id == " producer:example "
    assert grant.criteria_id == " criteria:complete:v1 "
    assert grant.origin is origin
    assert grant.method is method
    assert grant.allowed_assertions == frozenset({assertion})
    assert grant.model_id == base.model_id
    assert grant.model_version == base.model_version


def test_grant_can_explicitly_allow_multiple_assertions() -> None:
    assertions = frozenset(SafetyEvidenceAssertion)
    assert replace(_authority(), allowed_assertions=assertions).allowed_assertions == assertions


def test_authority_is_frozen() -> None:
    grant = _authority()
    with pytest.raises(FrozenInstanceError):
        grant.producer_id = "other"  # type: ignore[misc]
    with pytest.raises(AttributeError):
        grant.allowed_assertions.add(SafetyEvidenceAssertion.INDICATES_PROHIBITED)  # type: ignore


def test_authority_has_exact_fields() -> None:
    assert {field.name for field in fields(SafetyEvidenceAuthority)} == {
        "producer_id",
        "criteria_id",
        "origin",
        "method",
        "allowed_assertions",
        "model_id",
        "model_version",
    }


@pytest.mark.parametrize("identifier", ["", " ", "\t\n", None, 42, False])
def test_invalid_producer_id(identifier: str) -> None:
    with pytest.raises(ValueError) as error:
        replace(_authority(), producer_id=identifier)
    assert str(error.value) == (
        "Safety evidence authority producer ID must not be empty or whitespace."
    )


@pytest.mark.parametrize("identifier", ["", " ", "\t\n", None, 42, False])
def test_invalid_criteria_id(identifier: str) -> None:
    with pytest.raises(ValueError) as error:
        replace(_authority(), criteria_id=identifier)
    assert str(error.value) == (
        "Safety evidence authority criteria ID must not be empty or whitespace."
    )


@pytest.mark.parametrize("origin", ["source_metadata", "invalid", None, SafetyEvidenceMethod.MODEL])
def test_invalid_origin(origin: SafetyEvidenceOrigin) -> None:
    with pytest.raises(ValueError) as error:
        replace(_authority(), origin=origin)
    assert str(error.value) == "Safety evidence authority origin must be a SafetyEvidenceOrigin."


@pytest.mark.parametrize(
    "method", ["unknown", "invalid", None, SafetyEvidenceOrigin.SOURCE_METADATA]
)
def test_invalid_method(method: SafetyEvidenceMethod) -> None:
    with pytest.raises(ValueError) as error:
        replace(_authority(), method=method)
    assert str(error.value) == "Safety evidence authority method must be a SafetyEvidenceMethod."


@pytest.mark.parametrize(
    "assertions", [None, [], (), {SafetyEvidenceAssertion.SUPPORTS_CLEARANCE}, "supports_clearance"]
)
def test_assertions_require_frozenset(assertions: frozenset[SafetyEvidenceAssertion]) -> None:
    with pytest.raises(ValueError) as error:
        replace(_authority(), allowed_assertions=assertions)
    assert str(error.value) == "Safety evidence authority allowed assertions must be a frozenset."


def test_assertions_must_not_be_empty() -> None:
    with pytest.raises(ValueError) as error:
        replace(_authority(), allowed_assertions=frozenset())
    assert str(error.value) == "Safety evidence authority allowed assertions must not be empty."


class _OtherAssertion(StrEnum):
    SUPPORTS_CLEARANCE = "supports_clearance"


@pytest.mark.parametrize(
    "assertion",
    ["supports_clearance", "invalid", None, 42, _OtherAssertion.SUPPORTS_CLEARANCE],
)
def test_assertions_require_actual_enum_members(assertion: SafetyEvidenceAssertion) -> None:
    with pytest.raises(ValueError) as error:
        replace(
            _authority(),
            allowed_assertions=frozenset({SafetyEvidenceAssertion.INSUFFICIENT, assertion}),
        )
    assert str(error.value) == (
        "Safety evidence authority allowed assertions must contain only "
        "SafetyEvidenceAssertion members."
    )


@pytest.mark.parametrize("identifier", [None, "", " \t\n", 42, False])
def test_model_requires_model_id(identifier: str | None) -> None:
    with pytest.raises(ValueError) as error:
        replace(_model_authority(), model_id=identifier)
    assert str(error.value) == "Model authority requires a non-empty model ID."


@pytest.mark.parametrize("version", [None, "", " \t\n", 42, False])
def test_model_requires_model_version(version: str | None) -> None:
    with pytest.raises(ValueError) as error:
        replace(_model_authority(), model_version=version)
    assert str(error.value) == "Model authority requires a non-empty model version."


@pytest.mark.parametrize("method", [SafetyEvidenceMethod.NON_MODEL, SafetyEvidenceMethod.UNKNOWN])
@pytest.mark.parametrize("identifier", ["model:example", ""])
def test_non_model_methods_forbid_model_id(method: SafetyEvidenceMethod, identifier: str) -> None:
    with pytest.raises(ValueError) as error:
        replace(_authority(), method=method, model_id=identifier)
    assert str(error.value) == "Model ID must be absent for non-model or unknown authority methods."


@pytest.mark.parametrize("method", [SafetyEvidenceMethod.NON_MODEL, SafetyEvidenceMethod.UNKNOWN])
@pytest.mark.parametrize("version", ["v1", ""])
def test_non_model_methods_forbid_model_version(method: SafetyEvidenceMethod, version: str) -> None:
    with pytest.raises(ValueError) as error:
        replace(_authority(), method=method, model_version=version)
    assert str(error.value) == (
        "Model version must be absent for non-model or unknown authority methods."
    )
