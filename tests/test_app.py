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


def test_cli_has_only_agreed_dependencies() -> None:
    allowed = {"argparse", "collections.abc", "pathlib", "artsniffer.commands"}
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
