"""Tests for the ordered pre-analysis content boundary."""

import ast
import sys
from dataclasses import FrozenInstanceError, asdict
from pathlib import Path
from typing import cast

import pytest

import artsniffer.content.pre_analysis as pre_analysis
from artsniffer.content.rating import ContentRating
from artsniffer.content.service_permissions import (
    ServiceContentPermissionDecision,
    ServiceContentPermissionReason,
    ServiceContentPermissions,
)
from artsniffer.profiles.content_policy import (
    ContentPolicyDecision,
    ContentPolicyReason,
    ProfileContentPolicy,
    ProfileContentPolicyMode,
    evaluate_content_policy,
)
from artsniffer.safety.decision import SafetyGateDecision, SafetyGateReason
from artsniffer.safety.subject import SafetyClearedSubject, SafetySubject


def _cleared_subject(content_hash: str = "opaque:hash-v1") -> SafetyClearedSubject:
    return SafetyClearedSubject(
        subject=SafetySubject("artwork:one", content_hash),
        criteria_id="criteria:complete:v1",
        decision=SafetyGateDecision(True, SafetyGateReason.CLEARED),
    )


def _max_policy(rating: ContentRating) -> ProfileContentPolicy:
    return ProfileContentPolicy(ProfileContentPolicyMode.MAX_RATING, rating)


def test_safety_cleared_subject_can_enter_boundary_and_is_preserved() -> None:
    cleared_subject = _cleared_subject("opaque:hash-v2")

    result = pre_analysis.evaluate_pre_analysis(
        cleared_subject,
        ContentRating.GENERAL,
        ServiceContentPermissions(),
        _max_policy(ContentRating.GENERAL),
    )

    assert result.approved
    assert result.safety_cleared_subject is cleared_subject
    assert result.safety_cleared_subject.subject.content_hash == "opaque:hash-v2"
    assert result.rating is ContentRating.GENERAL
    assert result.service_decision == ServiceContentPermissionDecision(
        True, ServiceContentPermissionReason.ALLOWED
    )
    assert result.profile_decision == ContentPolicyDecision(True, ContentPolicyReason.ALLOWED)


def test_service_rejection_short_circuits_profile_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    evaluate_service = pre_analysis.evaluate_service_content_permissions

    def record_service(
        permissions: ServiceContentPermissions, rating: ContentRating
    ) -> ServiceContentPermissionDecision:
        calls.append("service")
        return evaluate_service(permissions, rating)

    def fail_if_profile_called(
        policy: ProfileContentPolicy, rating: ContentRating
    ) -> ContentPolicyDecision:
        calls.append("profile")
        raise AssertionError("Profile evaluation must not follow service rejection.")

    monkeypatch.setattr(pre_analysis, "evaluate_service_content_permissions", record_service)
    monkeypatch.setattr(pre_analysis, "evaluate_content_policy", fail_if_profile_called)

    result = pre_analysis.evaluate_pre_analysis(
        _cleared_subject(),
        ContentRating.ADULT,
        ServiceContentPermissions(),
        _max_policy(ContentRating.ADULT),
    )

    assert calls == ["service"]
    assert not result.approved
    assert result.decision.reason is pre_analysis.PreAnalysisReason.SERVICE_ADULT_CONTENT_DISABLED
    assert result.profile_decision is None


def test_profile_rejection_follows_service_acceptance() -> None:
    result = pre_analysis.evaluate_pre_analysis(
        _cleared_subject(),
        ContentRating.MATURE,
        ServiceContentPermissions(),
        _max_policy(ContentRating.GENERAL),
    )

    assert result.service_decision.allowed
    assert result.profile_decision == ContentPolicyDecision(
        False, ContentPolicyReason.RATING_ABOVE_MAXIMUM
    )
    assert not result.approved
    assert result.decision.reason is pre_analysis.PreAnalysisReason.PROFILE_RATING_ABOVE_MAXIMUM


def test_both_service_and_profile_acceptance_are_required_for_approval(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    evaluate_service = pre_analysis.evaluate_service_content_permissions
    evaluate_profile = pre_analysis.evaluate_content_policy

    def record_service(
        permissions: ServiceContentPermissions, rating: ContentRating
    ) -> ServiceContentPermissionDecision:
        calls.append("service")
        return evaluate_service(permissions, rating)

    def record_profile(
        policy: ProfileContentPolicy, rating: ContentRating
    ) -> ContentPolicyDecision:
        calls.append("profile")
        return evaluate_profile(policy, rating)

    monkeypatch.setattr(pre_analysis, "evaluate_service_content_permissions", record_service)
    monkeypatch.setattr(pre_analysis, "evaluate_content_policy", record_profile)

    result = pre_analysis.evaluate_pre_analysis(
        _cleared_subject(),
        ContentRating.MATURE,
        ServiceContentPermissions(),
        _max_policy(ContentRating.MATURE),
    )

    assert result.service_decision.allowed
    assert result.profile_decision is not None and result.profile_decision.allowed
    assert result.approved
    assert result.decision.reason is pre_analysis.PreAnalysisReason.APPROVED
    assert calls == ["service", "profile"]


def test_adult_profile_policy_cannot_bypass_service_adult_disablement() -> None:
    adult_only_policy = ProfileContentPolicy(ProfileContentPolicyMode.ADULT_ONLY)
    assert evaluate_content_policy(adult_only_policy, ContentRating.ADULT).allowed

    result = pre_analysis.evaluate_pre_analysis(
        _cleared_subject(),
        ContentRating.ADULT,
        ServiceContentPermissions(adult_content_enabled=False),
        adult_only_policy,
    )

    assert not result.approved
    assert result.service_decision.reason is ServiceContentPermissionReason.ADULT_CONTENT_DISABLED
    assert result.profile_decision is None


def test_pre_analysis_reason_values_are_stable() -> None:
    assert {reason.name: reason.value for reason in pre_analysis.PreAnalysisReason} == {
        "APPROVED": "approved",
        "SERVICE_RATING_UNKNOWN": "service_rating_unknown",
        "SERVICE_ADULT_CONTENT_DISABLED": "service_adult_content_disabled",
        "PROFILE_RATING_ABOVE_MAXIMUM": "profile_rating_above_maximum",
        "PROFILE_ADULT_REQUIRED": "profile_adult_required",
    }


def test_unknown_rating_remains_rejected_at_service_gate() -> None:
    result = pre_analysis.evaluate_pre_analysis(
        _cleared_subject(),
        ContentRating.UNKNOWN,
        ServiceContentPermissions(adult_content_enabled=True),
        _max_policy(ContentRating.ADULT),
    )

    assert not result.approved
    assert result.decision.reason is pre_analysis.PreAnalysisReason.SERVICE_RATING_UNKNOWN
    assert result.service_decision.reason is ServiceContentPermissionReason.RATING_UNKNOWN
    assert result.profile_decision is None


@pytest.mark.parametrize(
    ("safety_cleared_subject", "rating", "permissions", "policy", "message"),
    [
        (
            cast(SafetyClearedSubject, object()),
            ContentRating.GENERAL,
            ServiceContentPermissions(),
            _max_policy(ContentRating.GENERAL),
            "Pre-analysis safety clearance must be a SafetyClearedSubject.",
        ),
        (
            _cleared_subject(),
            cast(ContentRating, "general"),
            ServiceContentPermissions(),
            _max_policy(ContentRating.GENERAL),
            "Pre-analysis content rating must be a ContentRating.",
        ),
        (
            _cleared_subject(),
            ContentRating.GENERAL,
            cast(ServiceContentPermissions, None),
            _max_policy(ContentRating.GENERAL),
            "Pre-analysis service permissions must be a ServiceContentPermissions.",
        ),
        (
            _cleared_subject(),
            ContentRating.GENERAL,
            ServiceContentPermissions(),
            cast(ProfileContentPolicy, None),
            "Pre-analysis profile policy must be a ProfileContentPolicy.",
        ),
    ],
)
def test_invalid_inputs_fail_clearly(
    safety_cleared_subject: SafetyClearedSubject,
    rating: ContentRating,
    permissions: ServiceContentPermissions,
    policy: ProfileContentPolicy,
    message: str,
) -> None:
    with pytest.raises(ValueError) as error:
        pre_analysis.evaluate_pre_analysis(safety_cleared_subject, rating, permissions, policy)

    assert str(error.value) == message


def test_evaluation_does_not_mutate_inputs() -> None:
    safety_cleared_subject = _cleared_subject()
    permissions = ServiceContentPermissions(adult_content_enabled=True)
    policy = ProfileContentPolicy(ProfileContentPolicyMode.ADULT_ONLY)
    before = tuple(asdict(item) for item in (safety_cleared_subject, permissions, policy))

    pre_analysis.evaluate_pre_analysis(
        safety_cleared_subject,
        ContentRating.ADULT,
        permissions,
        policy,
    )

    assert tuple(asdict(item) for item in (safety_cleared_subject, permissions, policy)) == before


def test_result_is_immutable() -> None:
    result = pre_analysis.evaluate_pre_analysis(
        _cleared_subject(),
        ContentRating.GENERAL,
        ServiceContentPermissions(),
        _max_policy(ContentRating.GENERAL),
    )

    with pytest.raises(FrozenInstanceError):
        result.rating = ContentRating.ADULT  # type: ignore[misc]


_VALID_SAFETY_CLEARED_SUBJECT = _cleared_subject()

_VALID_PRE_ANALYSIS_DECISION = pre_analysis.PreAnalysisDecision(
    pre_analysis.PreAnalysisReason.APPROVED
)

_ALLOWED_SERVICE_DECISION = ServiceContentPermissionDecision(
    True, ServiceContentPermissionReason.ALLOWED
)

_ALLOWED_PROFILE_DECISION = ContentPolicyDecision(True, ContentPolicyReason.ALLOWED)


def _result(
    *,
    safety_cleared_subject: SafetyClearedSubject = _VALID_SAFETY_CLEARED_SUBJECT,
    rating: ContentRating = ContentRating.GENERAL,
    decision: pre_analysis.PreAnalysisDecision = _VALID_PRE_ANALYSIS_DECISION,
    service_decision: ServiceContentPermissionDecision = _ALLOWED_SERVICE_DECISION,
    profile_decision: ContentPolicyDecision | None = _ALLOWED_PROFILE_DECISION,
) -> pre_analysis.PreAnalysisResult:
    return pre_analysis.PreAnalysisResult(
        safety_cleared_subject,
        rating,
        decision,
        service_decision,
        profile_decision,
    )


def test_pre_analysis_decision_rejects_non_reason() -> None:
    with pytest.raises(ValueError, match="^Pre-analysis reason must be a PreAnalysisReason\\.$"):
        pre_analysis.PreAnalysisDecision(cast(pre_analysis.PreAnalysisReason, "approved"))


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        (
            "safety_cleared_subject",
            cast(SafetyClearedSubject, object()),
            "Pre-analysis result requires a SafetyClearedSubject.",
        ),
        (
            "rating",
            cast(ContentRating, "general"),
            "Pre-analysis result rating must be a ContentRating.",
        ),
        (
            "decision",
            cast(pre_analysis.PreAnalysisDecision, object()),
            "Pre-analysis result decision must be a PreAnalysisDecision.",
        ),
        (
            "service_decision",
            cast(ServiceContentPermissionDecision, object()),
            "Pre-analysis result service decision must be a ServiceContentPermissionDecision.",
        ),
        (
            "profile_decision",
            cast(ContentPolicyDecision, object()),
            "Service acceptance requires a ContentPolicyDecision for the profile.",
        ),
    ],
)
def test_pre_analysis_result_rejects_malformed_field_types(
    field: str, value: object, message: str
) -> None:
    values: dict[str, object] = {
        "safety_cleared_subject": _cleared_subject(),
        "rating": ContentRating.GENERAL,
        "decision": pre_analysis.PreAnalysisDecision(pre_analysis.PreAnalysisReason.APPROVED),
        "service_decision": ServiceContentPermissionDecision(
            True, ServiceContentPermissionReason.ALLOWED
        ),
        "profile_decision": ContentPolicyDecision(True, ContentPolicyReason.ALLOWED),
    }
    values[field] = value

    with pytest.raises(ValueError) as error:
        pre_analysis.PreAnalysisResult(
            cast(SafetyClearedSubject, values["safety_cleared_subject"]),
            cast(ContentRating, values["rating"]),
            cast(pre_analysis.PreAnalysisDecision, values["decision"]),
            cast(ServiceContentPermissionDecision, values["service_decision"]),
            cast(ContentPolicyDecision | None, values["profile_decision"]),
        )

    assert str(error.value) == message


def test_service_rejection_cannot_include_profile_decision() -> None:
    with pytest.raises(
        ValueError, match="^Service rejection must not include a profile decision\\.$"
    ):
        _result(
            decision=pre_analysis.PreAnalysisDecision(
                pre_analysis.PreAnalysisReason.SERVICE_ADULT_CONTENT_DISABLED
            ),
            service_decision=ServiceContentPermissionDecision(
                False, ServiceContentPermissionReason.ADULT_CONTENT_DISABLED
            ),
        )


def test_service_acceptance_requires_profile_decision() -> None:
    with pytest.raises(
        ValueError,
        match="^Service acceptance requires a ContentPolicyDecision for the profile\\.$",
    ):
        _result(profile_decision=None)


@pytest.mark.parametrize(
    ("decision_reason", "service_decision", "profile_decision"),
    [
        (
            pre_analysis.PreAnalysisReason.SERVICE_RATING_UNKNOWN,
            ServiceContentPermissionDecision(True, ServiceContentPermissionReason.ALLOWED),
            ContentPolicyDecision(True, ContentPolicyReason.ALLOWED),
        ),
        (
            pre_analysis.PreAnalysisReason.PROFILE_RATING_ABOVE_MAXIMUM,
            ServiceContentPermissionDecision(True, ServiceContentPermissionReason.ALLOWED),
            ContentPolicyDecision(True, ContentPolicyReason.ALLOWED),
        ),
        (
            pre_analysis.PreAnalysisReason.APPROVED,
            ServiceContentPermissionDecision(True, ServiceContentPermissionReason.ALLOWED),
            ContentPolicyDecision(False, ContentPolicyReason.RATING_ABOVE_MAXIMUM),
        ),
    ],
)
def test_composed_reason_must_match_component_decisions(
    decision_reason: pre_analysis.PreAnalysisReason,
    service_decision: ServiceContentPermissionDecision,
    profile_decision: ContentPolicyDecision,
) -> None:
    with pytest.raises(
        ValueError, match="^Pre-analysis reason must agree with component decisions\\.$"
    ):
        _result(
            decision=pre_analysis.PreAnalysisDecision(decision_reason),
            service_decision=service_decision,
            profile_decision=profile_decision,
        )


@pytest.mark.parametrize(
    ("service_decision", "profile_decision"),
    [
        (
            ServiceContentPermissionDecision(
                False, ServiceContentPermissionReason.ADULT_CONTENT_DISABLED
            ),
            None,
        ),
        (
            ServiceContentPermissionDecision(True, ServiceContentPermissionReason.ALLOWED),
            ContentPolicyDecision(False, ContentPolicyReason.RATING_ABOVE_MAXIMUM),
        ),
    ],
)
def test_approval_requires_both_component_decisions_to_allow(
    service_decision: ServiceContentPermissionDecision,
    profile_decision: ContentPolicyDecision | None,
) -> None:
    with pytest.raises(
        ValueError, match="^Pre-analysis reason must agree with component decisions\\.$"
    ):
        _result(
            decision=pre_analysis.PreAnalysisDecision(pre_analysis.PreAnalysisReason.APPROVED),
            service_decision=service_decision,
            profile_decision=profile_decision,
        )


def test_pre_analysis_decision_and_result_are_immutable() -> None:
    decision = pre_analysis.PreAnalysisDecision(pre_analysis.PreAnalysisReason.APPROVED)
    result = _result()

    with pytest.raises(FrozenInstanceError):
        decision.reason = pre_analysis.PreAnalysisReason.PROFILE_RATING_ABOVE_MAXIMUM  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        result.decision = pre_analysis.PreAnalysisDecision(  # type: ignore[misc]
            pre_analysis.PreAnalysisReason.PROFILE_RATING_ABOVE_MAXIMUM
        )


def test_pre_analysis_module_has_no_provider_recommendation_or_destination_dependencies() -> None:
    module_path = (
        Path(__file__).resolve().parents[2] / "src" / "artsniffer" / "content" / "pre_analysis.py"
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    allowed_artsniffer_modules = {
        "artsniffer.content.rating",
        "artsniffer.content.service_permissions",
        "artsniffer.profiles.content_policy",
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
                or module in allowed_artsniffer_modules
            ), f"Unexpected dependency: {module}"
