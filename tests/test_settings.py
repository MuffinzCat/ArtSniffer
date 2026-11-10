"""Tests for loading and validating application settings."""

import tomllib
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from artsniffer.settings import (
    ArtSnifferSettings,
    LocalReferenceLibrarySettings,
    find_config_path,
    load_settings,
    parse_local_reference_library,
)


@pytest.fixture
def clean_config_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for variable in ("ARTSNIFFER_CONFIG", "LOCALAPPDATA", "XDG_CONFIG_HOME", "HOME"):
        monkeypatch.delenv(variable, raising=False)


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


def test_find_config_path_accepts_an_existing_relative_explicit_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    clean_config_environment: None,
) -> None:
    monkeypatch.chdir(tmp_path)
    config_path = Path("settings/config.toml")
    config_path.parent.mkdir()
    config_path.write_text("", encoding="utf-8")

    assert find_config_path(config_path) == config_path


def test_find_config_path_accepts_an_existing_absolute_explicit_path(
    tmp_path: Path, clean_config_environment: None
) -> None:
    config_path = (tmp_path / "config.toml").resolve()
    config_path.write_text("", encoding="utf-8")

    assert find_config_path(config_path) == config_path


@pytest.mark.parametrize("as_directory", [False, True])
def test_find_config_path_rejects_an_explicit_path_that_is_not_a_file(
    tmp_path: Path, as_directory: bool, clean_config_environment: None
) -> None:
    config_path = tmp_path / "not-a-file"
    if as_directory:
        config_path.mkdir()

    with pytest.raises(FileNotFoundError) as error:
        find_config_path(config_path)

    assert str(config_path) in str(error.value)


def test_find_config_path_prefers_explicit_path_over_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    clean_config_environment: None,
) -> None:
    explicit_path = tmp_path / "explicit.toml"
    environment_path = tmp_path / "environment.toml"
    explicit_path.write_text("", encoding="utf-8")
    environment_path.write_text("", encoding="utf-8")
    monkeypatch.setenv("ARTSNIFFER_CONFIG", str(environment_path))

    assert find_config_path(explicit_path) == explicit_path


def test_find_config_path_uses_an_existing_absolute_environment_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    clean_config_environment: None,
) -> None:
    config_path = (tmp_path / "environment.toml").resolve()
    config_path.write_text("", encoding="utf-8")
    monkeypatch.setenv("ARTSNIFFER_CONFIG", str(config_path))

    assert find_config_path(None) == config_path


@pytest.mark.parametrize("value", ["", " \t "])
def test_find_config_path_treats_empty_environment_override_as_unset(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    clean_config_environment: None,
    value: str,
) -> None:
    home = tmp_path.resolve()
    monkeypatch.setattr("artsniffer.settings.sys.platform", "linux")
    monkeypatch.setenv("ARTSNIFFER_CONFIG", value)
    monkeypatch.setenv("HOME", str(home))

    assert find_config_path(None) == home / ".config" / "artsniffer" / "config.toml"


def test_find_config_path_rejects_a_relative_environment_override(
    monkeypatch: pytest.MonkeyPatch, clean_config_environment: None
) -> None:
    monkeypatch.setenv("ARTSNIFFER_CONFIG", "relative/config.toml")

    with pytest.raises(RuntimeError, match="ARTSNIFFER_CONFIG.*absolute path"):
        find_config_path(None)


def test_find_config_path_reports_a_missing_environment_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    clean_config_environment: None,
) -> None:
    config_path = (tmp_path / "missing.toml").resolve()
    monkeypatch.setenv("ARTSNIFFER_CONFIG", str(config_path))

    with pytest.raises(FileNotFoundError) as error:
        find_config_path(None)

    assert str(config_path) in str(error.value)


def test_find_config_path_uses_the_windows_local_appdata_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    clean_config_environment: None,
) -> None:
    local_appdata = tmp_path.resolve()
    monkeypatch.setattr("artsniffer.settings.sys.platform", "win32")
    monkeypatch.setenv("LOCALAPPDATA", str(local_appdata))

    assert find_config_path(None) == local_appdata / "ArtSniffer" / "config.toml"


@pytest.mark.parametrize("local_appdata", [None, "", "relative/path"])
def test_find_config_path_fails_without_absolute_windows_local_appdata(
    monkeypatch: pytest.MonkeyPatch,
    clean_config_environment: None,
    local_appdata: str | None,
) -> None:
    monkeypatch.setattr("artsniffer.settings.sys.platform", "win32")
    if local_appdata is not None:
        monkeypatch.setenv("LOCALAPPDATA", local_appdata)

    with pytest.raises(RuntimeError, match="could not determine a default configuration"):
        find_config_path(None)


def test_find_config_path_uses_absolute_linux_xdg_config_home(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    clean_config_environment: None,
) -> None:
    xdg_config_home = tmp_path.resolve()
    monkeypatch.setattr("artsniffer.settings.sys.platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg_config_home))
    monkeypatch.setenv("HOME", str(tmp_path / "unused-home"))

    assert find_config_path(None) == xdg_config_home / "artsniffer" / "config.toml"


def test_find_config_path_ignores_relative_xdg_config_home(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    clean_config_environment: None,
) -> None:
    home = tmp_path.resolve()
    monkeypatch.setattr("artsniffer.settings.sys.platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", "relative/xdg")
    monkeypatch.setenv("HOME", str(home))

    assert find_config_path(None) == home / ".config" / "artsniffer" / "config.toml"


@pytest.mark.parametrize("xdg_config_home", [None, ""])
def test_find_config_path_uses_home_when_xdg_config_home_is_empty_or_unset(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    clean_config_environment: None,
    xdg_config_home: str | None,
) -> None:
    home = tmp_path.resolve()
    monkeypatch.setattr("artsniffer.settings.sys.platform", "linux")
    monkeypatch.setenv("HOME", str(home))
    if xdg_config_home is not None:
        monkeypatch.setenv("XDG_CONFIG_HOME", xdg_config_home)

    assert find_config_path(None) == home / ".config" / "artsniffer" / "config.toml"


@pytest.mark.parametrize("home", [None, "", "relative/home"])
def test_find_config_path_fails_without_absolute_linux_home(
    monkeypatch: pytest.MonkeyPatch,
    clean_config_environment: None,
    home: str | None,
) -> None:
    monkeypatch.setattr("artsniffer.settings.sys.platform", "linux")
    if home is not None:
        monkeypatch.setenv("HOME", home)

    with pytest.raises(RuntimeError, match="could not determine a default configuration"):
        find_config_path(None)


def test_find_config_path_rejects_an_unsupported_platform(
    monkeypatch: pytest.MonkeyPatch, clean_config_environment: None
) -> None:
    monkeypatch.setattr("artsniffer.settings.sys.platform", "darwin")

    with pytest.raises(RuntimeError, match="could not determine a default configuration"):
        find_config_path(None)


def test_find_config_path_does_not_discover_config_in_current_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    clean_config_environment: None,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("artsniffer.settings.sys.platform", "linux")
    Path("config.toml").write_text("", encoding="utf-8")

    with pytest.raises(RuntimeError, match="could not determine a default configuration"):
        find_config_path(None)
