"""Tests for loading and validating application settings."""

import tomllib
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from artsniffer.settings import (
    ArtSnifferSettings,
    LocalReferenceLibrarySettings,
    load_settings,
    parse_local_reference_library,
)


def test_empty_configuration_has_no_reference_libraries(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text("", encoding="utf-8")

    assert load_settings(config_path) == ArtSnifferSettings(reference_libraries=())


def test_loads_one_reference_library_and_resolves_relative_paths(tmp_path: Path) -> None:
    config_path = tmp_path / "settings" / "config.toml"
    config_path.parent.mkdir()
    config_path.write_text(
        """
[[reference_libraries]]
source_id = "local"
folder = "artworks"
state_file = "state/library.json"
""",
        encoding="utf-8",
    )

    settings = load_settings(config_path)

    assert settings.reference_libraries == (
        LocalReferenceLibrarySettings(
            source_id="local",
            folder=config_path.parent / "artworks",
            state_file=config_path.parent / "state" / "library.json",
        ),
    )


def test_loads_multiple_reference_libraries_in_configuration_order(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        """
[[reference_libraries]]
source_id = "first"
folder = "one"
state_file = "one.json"

[[reference_libraries]]
source_id = "second"
folder = "two"
state_file = "two.json"
""",
        encoding="utf-8",
    )

    settings = load_settings(config_path)

    assert tuple(library.source_id for library in settings.reference_libraries) == (
        "first",
        "second",
    )
    assert tuple(library.folder for library in settings.reference_libraries) == (
        tmp_path / "one",
        tmp_path / "two",
    )
    assert tuple(library.state_file for library in settings.reference_libraries) == (
        tmp_path / "one.json",
        tmp_path / "two.json",
    )


def test_absolute_paths_are_not_resolved_against_config_directory(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    folder = (tmp_path / "absolute-artworks").resolve()
    state_file = (tmp_path / "absolute-state.json").resolve()
    config_path.write_text(
        f"""
[[reference_libraries]]
source_id = "local"
folder = '{folder}'
state_file = '{state_file}'
""",
        encoding="utf-8",
    )

    library = load_settings(config_path).reference_libraries[0]

    assert library.folder == folder
    assert library.state_file == state_file


@pytest.mark.parametrize(
    ("library_data", "message"),
    [
        ({}, "source ID must be a string"),
        ({"source_id": 12}, "source ID must be a string"),
        (
            {"source_id": " \t ", "folder": "artworks", "state_file": "state.json"},
            "source ID cannot be empty or whitespace",
        ),
        ({"source_id": "local"}, "folder must be a string"),
        ({"source_id": "local", "folder": 12}, "folder must be a string"),
        (
            {"source_id": "local", "folder": "artworks", "state_file": " \t "},
            "state file cannot be empty or whitespace",
        ),
        (
            {"source_id": "local", "folder": "artworks"},
            "state file must be a string",
        ),
        (
            {"source_id": "local", "folder": " \t ", "state_file": "state.json"},
            "folder cannot be empty or whitespace",
        ),
        (
            {"source_id": "local", "folder": "artworks", "state_file": 12},
            "state file must be a string",
        ),
    ],
)
def test_invalid_reference_library_values_are_rejected(
    tmp_path: Path, library_data: dict[str, object], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        parse_local_reference_library(library_data, tmp_path)


def test_missing_reference_libraries_means_no_libraries(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text("title = 'settings without libraries'\n", encoding="utf-8")

    assert load_settings(config_path) == ArtSnifferSettings(reference_libraries=())


@pytest.mark.parametrize(
    ("toml", "message"),
    [
        ("reference_libraries = 'not a list'\n", "reference_libraries must be a list"),
        ("reference_libraries = ['not a table']\n", "each reference library must be a dictionary"),
    ],
)
def test_invalid_reference_libraries_value_is_rejected(
    tmp_path: Path, toml: str, message: str
) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(toml, encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        load_settings(config_path)


def test_duplicate_source_ids_are_rejected(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        """
[[reference_libraries]]
source_id = "local"
folder = "one"
state_file = "one.json"

[[reference_libraries]]
source_id = "local"
folder = "two"
state_file = "two.json"
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate source ID: local"):
        load_settings(config_path)


def test_malformed_toml_is_reported(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text("reference_libraries = [\n", encoding="utf-8")

    with pytest.raises(tomllib.TOMLDecodeError):
        load_settings(config_path)


def test_missing_config_file_error_is_propagated(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_settings(tmp_path / "missing.toml")


def test_settings_records_are_immutable(tmp_path: Path) -> None:
    library = LocalReferenceLibrarySettings(
        source_id="local",
        folder=tmp_path / "artworks",
        state_file=tmp_path / "state.json",
    )
    settings = ArtSnifferSettings(reference_libraries=(library,))
    library_attribute = "source_id"
    settings_attribute = "reference_libraries"

    with pytest.raises(FrozenInstanceError):
        setattr(library, library_attribute, "other")
    with pytest.raises(FrozenInstanceError):
        setattr(settings, settings_attribute, ())
