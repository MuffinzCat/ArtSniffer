"""Tests for installation-level content permissions."""

from dataclasses import FrozenInstanceError, fields
from typing import cast

import pytest

from artsniffer.content.service_permissions import ServiceContentPermissions
from artsniffer.profiles.content_policy import ProfileContentPolicy


def test_adult_content_is_disabled_by_default() -> None:
    assert ServiceContentPermissions().adult_content_enabled is False


@pytest.mark.parametrize("enabled", [False, True])
def test_explicit_adult_enablement_is_preserved(enabled: bool) -> None:
    assert ServiceContentPermissions(adult_content_enabled=enabled).adult_content_enabled is enabled


def test_permissions_have_only_installation_level_fields() -> None:
    assert {field.name for field in fields(ServiceContentPermissions)} == {"adult_content_enabled"}
    assert not isinstance(ServiceContentPermissions(), ProfileContentPolicy)


def test_permissions_are_immutable() -> None:
    permissions = ServiceContentPermissions()

    with pytest.raises(FrozenInstanceError):
        permissions.adult_content_enabled = True  # type: ignore[misc]


@pytest.mark.parametrize("value", [None, 0, 1, "false", "true", object()])
def test_permissions_reject_non_boolean_enablement(value: object) -> None:
    with pytest.raises(ValueError) as error:
        ServiceContentPermissions(adult_content_enabled=cast(bool, value))

    assert str(error.value) == "Service adult-content enablement must be a bool."
