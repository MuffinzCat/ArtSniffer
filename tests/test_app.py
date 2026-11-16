"""Synthetic top-level CLI and entry-point tests; no external services."""

import argparse
import ast
import json
import shutil
import subprocess
from pathlib import Path
from unittest.mock import Mock

import pytest

import artsniffer.cli as cli
from artsniffer import main


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (["--help"], "references"),
        (["references", "--help"], "scan-local"),
        (["references", "--help"], "diff-local"),
        (["references", "--help"], "snapshot"),
        (["references", "--help"], "refresh-local"),
        (["references", "snapshot", "--help"], "validate"),
        (["references", "refresh-local", "--help"], "--dry-run"),
        (["references", "scan-local", "--help"], "--source-id"),
        (["references", "diff-local", "--help"], "--against"),
    ],
)
def test_help(argv: list[str], expected: str, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as error:
        main(argv)
    assert error.value.code == 0
    captured = capsys.readouterr()
    assert "usage: artsniffer" in captured.out
    assert expected in captured.out
    assert captured.err == ""


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["unknown"],
        ["references"],
        ["references", "unknown"],
        ["references", "scan-local"],
        ["references", "scan-local", "library"],
        ["references", "scan-local", "--source-id", "local"],
        ["references", "scan-local", "library", "--source-id"],
        ["references", "scan-local", "library", "--source-id", "local", "--unknown"],
        ["references", "diff-local"],
        ["references", "diff-local", "library", "--source-id", "local"],
        ["references", "diff-local", "library", "--against", "baseline.json"],
        ["references", "diff-local", "library", "--source-id", "local", "--against"],
    ],
)
def test_usage_errors(argv: list[str], capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as error:
        main(argv)
    assert error.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "usage: artsniffer" in captured.err
    assert "error:" in captured.err
    assert "Traceback" not in captured.err


@pytest.mark.parametrize("command", ["scan-local", "diff-local"])
def test_main_dispatches_to_selected_handler(
    command: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    handler = Mock(return_value=7)
    monkeypatch.setattr(cli.references, "run_local_reference_command", handler)
    argv = ["references", command, "library", "--source-id", "local", "--json"]
    if command == "diff-local":
        argv.extend(["--against", "baseline.json"])

    assert main(argv) == 7
    handler.assert_called_once()
    args = handler.call_args.args[0]
    assert isinstance(args, argparse.Namespace)
    assert args.command == "references"
    assert args.reference_command == command
    assert args.root == "library"
    assert args.source_id == "local"
    assert args.json is True
    assert args.config is None
    if command == "diff-local":
        assert args.against == "baseline.json"
    captured = capsys.readouterr()
    assert captured.out == captured.err == ""


@pytest.mark.parametrize(
    ("config_arguments", "expected_config"),
    [
        ([], None),
        (["--config", "missing.toml"], Path("missing.toml")),
    ],
)
def test_config_option_is_optional_and_parsed_as_a_path(
    config_arguments: list[str],
    expected_config: Path | None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    handler = Mock(return_value=0)
    monkeypatch.setattr(cli.references, "run_local_reference_command", handler)

    assert (
        main(
            [
                *config_arguments,
                "references",
                "scan-local",
                "library",
                "--source-id",
                "local",
            ]
        )
        == 0
    )

    parsed_config = handler.call_args.args[0].config
    assert parsed_config == expected_config
    if expected_config is not None:
        assert isinstance(parsed_config, Path)


def test_observe_loads_explicit_config_and_reports_each_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    config_directory = tmp_path / "settings"
    config_directory.mkdir()
    library_a = config_directory / "library-a"
    library_a.mkdir()
    (library_a / "one.png").write_bytes(b"one")
    (library_a / "two.jpg").write_bytes(b"two")
    library_b = config_directory / "library-b"
    library_b.mkdir()
    (library_b / "three.webp").write_bytes(b"three")
    config_path = config_directory / "config.toml"
    original_config = (
        b'[[reference_libraries]]\nsource_id = "source-a"\nfolder = "library-a"\n'
        b'state_file = "state-a.json"\n\n[[reference_libraries]]\n'
        b'source_id = "source-b"\nfolder = "library-b"\nstate_file = "state-b.json"\n'
    )
    config_path.write_bytes(original_config)
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ARTSNIFFER_CONFIG", raising=False)

    assert main(["--config", str(config_path), "observe"]) == 0

    captured = capsys.readouterr()
    assert captured.out == (
        "Source: source-a\n"
        "Observed reference items: 2\n"
        "Source: source-b\n"
        "Observed reference items: 1\n"
    )
    assert captured.err == ""
    assert config_path.read_bytes() == original_config


def test_observe_with_no_configured_libraries_is_quiet(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text("reference_libraries = []\n", encoding="utf-8")
    monkeypatch.delenv("ARTSNIFFER_CONFIG", raising=False)

    assert main(["--config", str(config_path), "observe"]) == 0
    captured = capsys.readouterr()
    assert captured.out == captured.err == ""


def test_observe_explicit_missing_config_is_an_error_without_creation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    config_path = tmp_path / "missing.toml"
    monkeypatch.delenv("ARTSNIFFER_CONFIG", raising=False)

    assert main(["--config", str(config_path), "observe"]) == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == (
        f"artsniffer: error: Configuration file does not exist or is not a file: {config_path}\n"
    )
    assert "Traceback" not in captured.err
    assert not config_path.exists()


def test_observe_missing_environment_config_is_an_error_without_creation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    config_path = (tmp_path / "missing.toml").resolve()
    monkeypatch.setenv("ARTSNIFFER_CONFIG", str(config_path))

    assert main(["observe"]) == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == (
        f"artsniffer: error: Configuration file does not exist or is not a file: {config_path}\n"
    )
    assert "Traceback" not in captured.err
    assert not config_path.exists()


def test_observe_creates_the_discovered_default_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("artsniffer.settings.sys.platform", "win32")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path.resolve()))
    monkeypatch.delenv("ARTSNIFFER_CONFIG", raising=False)
    config_path = tmp_path / "ArtSniffer" / "config.toml"

    assert main(["observe"]) == 0

    captured = capsys.readouterr()
    assert captured.out == captured.err == ""
    assert config_path.read_bytes() == b"reference_libraries = []\n"


def test_observe_reports_configuration_loading_errors_concisely(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    config_path = tmp_path / "invalid.toml"
    config_path.write_text("reference_libraries = [\n", encoding="utf-8")
    monkeypatch.delenv("ARTSNIFFER_CONFIG", raising=False)

    assert main(["--config", str(config_path), "observe"]) == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("artsniffer: error: ")
    assert "Traceback" not in captured.err


@pytest.mark.parametrize(
    ("failure_at", "error"),
    [
        ("discovery", RuntimeError("configuration location unavailable")),
        ("creation", PermissionError("configuration directory is read-only")),
        ("loading", ValueError("configuration cannot be loaded")),
    ],
)
def test_observe_reports_configuration_stage_failures_concisely(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    failure_at: str,
    error: Exception,
) -> None:
    config_path = tmp_path / "config.toml"
    monkeypatch.setattr(cli, "find_config_path", Mock(return_value=config_path))
    monkeypatch.setattr(cli, "create_initial_config", Mock(return_value=False))
    monkeypatch.setattr(cli, "load_settings", Mock(return_value=Mock()))
    if failure_at == "discovery":
        monkeypatch.setattr(cli, "find_config_path", Mock(side_effect=error))
    elif failure_at == "creation":
        monkeypatch.setattr(cli, "create_initial_config", Mock(side_effect=error))
    else:
        monkeypatch.setattr(cli, "load_settings", Mock(side_effect=error))

    assert main(["observe"]) == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == f"artsniffer: error: {error}\n"
    assert "Traceback" not in captured.err


@pytest.mark.parametrize("error", [OSError("library unavailable"), ValueError("invalid library")])
def test_observe_reports_expected_provider_errors_concisely(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    error: Exception,
) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text("reference_libraries = []\n", encoding="utf-8")
    monkeypatch.delenv("ARTSNIFFER_CONFIG", raising=False)
    monkeypatch.setattr(cli, "inspect_sources", Mock(side_effect=error))

    assert main(["--config", str(config_path), "observe"]) == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == f"artsniffer: error: {error}\n"
    assert "Traceback" not in captured.err


@pytest.mark.parametrize(
    "error",
    [
        RuntimeError("provider programming failure"),
        TypeError("provider programming failure"),
        AssertionError("provider programming failure"),
    ],
)
def test_observe_does_not_hide_unexpected_provider_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, error: Exception
) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text("reference_libraries = []\n", encoding="utf-8")
    monkeypatch.delenv("ARTSNIFFER_CONFIG", raising=False)
    monkeypatch.setattr(cli, "inspect_sources", Mock(side_effect=error))

    with pytest.raises(type(error), match="provider programming failure") as raised:
        main(["--config", str(config_path), "observe"])

    assert raised.value is error


def test_one_off_reference_command_does_not_require_application_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        cli,
        "find_config_path",
        Mock(side_effect=AssertionError("one-off commands must not load application settings")),
    )

    assert (
        main(["references", "scan-local", str(tmp_path), "--source-id", "one-off", "--json"]) == 0
    )

    captured = capsys.readouterr()
    assert json.loads(captured.out)["item_count"] == 0
    assert captured.err == ""


def test_cli_has_only_agreed_dependencies() -> None:
    allowed = {
        "argparse",
        "collections.abc",
        "pathlib",
        "sys",
        "artsniffer.commands",
        "artsniffer.reference_application",
        "artsniffer.settings",
    }
    for node in ast.walk(ast.parse(Path(cli.__file__).read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            assert all(alias.name in allowed for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            assert node.module in allowed


@pytest.mark.parametrize("failure", [False, True])
def test_installed_entry_point_exit_status(tmp_path: Path, failure: bool) -> None:
    executable = shutil.which("artsniffer")
    assert executable is not None
    root = tmp_path / "missing" if failure else tmp_path
    result = subprocess.run(
        [executable, "references", "scan-local", str(root), "--source-id", "local", "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    if failure:
        assert result.returncode == 1
        assert result.stdout == ""
        assert "artsniffer: error:" in result.stderr
        assert "Traceback" not in result.stderr
    else:
        assert result.returncode == 0
        assert json.loads(result.stdout)["item_count"] == 0
        assert result.stderr == ""
