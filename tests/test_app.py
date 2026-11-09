"""Synthetic command-line tests; no real artwork or external services."""

import ast
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path
from unittest.mock import Mock

import pytest

import artsniffer.cli as cli
from artsniffer import main
from artsniffer.references.observation import ReferenceItemObservation


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (["--help"], "references"),
        (["references", "--help"], "scan-local"),
        (["references", "scan-local", "--help"], "--source-id"),
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


@pytest.mark.parametrize("as_json", [False, True])
def test_empty_scan(tmp_path: Path, capsys: pytest.CaptureFixture[str], as_json: bool) -> None:
    argv = ["references", "scan-local", str(tmp_path), "--source-id", "local"]
    assert main(argv + (["--json"] if as_json else [])) == 0
    captured = capsys.readouterr()
    if as_json:
        assert json.loads(captured.out) == {
            "source_id": "local",
            "root": str(tmp_path),
            "item_count": 0,
            "items": [],
        }
    else:
        assert captured.out == f"Source: local\nRoot: {tmp_path}\nObserved reference items: 0\n"
    assert captured.err == ""


@pytest.mark.parametrize("as_json", [False, True])
def test_populated_scan_preserves_order_values_and_supplied_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    as_json: bool,
) -> None:
    root = tmp_path / "library with spaces"
    root.mkdir()
    (root / "nested folder").mkdir()
    contents = {"z.png": b"z", "nested folder/a.JPG": b"abc", ".hidden.webp": b""}
    for name, content in contents.items():
        root.joinpath(*name.split("/")).write_bytes(content)
    (root / "ignored.txt").write_bytes(b"not an image")
    monkeypatch.chdir(tmp_path)
    supplied_root = f".{os.sep}{root.name}"
    argv = ["references", "scan-local", supplied_root, "--source-id", " exact source "]
    if as_json:
        argv.append("--json")

    assert main(argv) == 0
    first = capsys.readouterr()
    assert main(argv) == 0
    assert capsys.readouterr() == first
    assert first.err == ""
    if as_json:
        assert json.loads(first.out) == {
            "source_id": " exact source ",
            "root": supplied_root,
            "item_count": 3,
            "items": [
                {
                    "source_item_id": name,
                    "content_hash": f"sha256:{hashlib.sha256(contents[name]).hexdigest()}",
                }
                for name in sorted(contents)
            ],
        }
    else:
        assert first.out.splitlines() == [
            "Source:  exact source ",
            f"Root: {supplied_root}",
            "Observed reference items: 3",
            *sorted(contents),
        ]


@pytest.mark.parametrize("as_json", [False, True])
@pytest.mark.parametrize("failure", ["missing", "file", "source-id"])
def test_real_provider_errors(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], failure: str, as_json: bool
) -> None:
    root = tmp_path
    source_id = "local"
    if failure == "missing":
        root = tmp_path / "missing"
        message = repr(str(root))
    elif failure == "file":
        root = tmp_path / "file.png"
        root.write_bytes(b"abc")
        message = f"Reference root must be a directory: {root}."
    else:
        source_id = " "
        message = "Source ID must not be empty or whitespace."
    argv = ["references", "scan-local", str(root), "--source-id", source_id]

    assert main(argv + (["--json"] if as_json else [])) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert message in captured.err
    assert captured.err.startswith("artsniffer: error: ")
    assert "Traceback" not in captured.err


@pytest.mark.parametrize("as_json", [False, True])
def test_cli_only_constructs_and_observes_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    as_json: bool,
) -> None:
    items = (
        ReferenceItemObservation("source", "z.opaque", "hash-z"),
        ReferenceItemObservation("source", "a.opaque", "hash-a"),
    )
    provider = Mock(spec=["observe"])
    provider.observe.return_value = items
    constructor = Mock(return_value=provider)
    monkeypatch.setattr(cli, "LocalFilesystemReferenceProvider", constructor)
    argv = ["references", "scan-local", str(tmp_path), "--source-id", "source"]

    assert main(argv + (["--json"] if as_json else [])) == 0
    constructor.assert_called_once_with(source_id="source", root=tmp_path)
    provider.observe.assert_called_once_with()
    captured = capsys.readouterr()
    if as_json:
        assert json.loads(captured.out)["items"] == [
            {"source_item_id": item.source_item_id, "content_hash": item.content_hash}
            for item in items
        ]
    else:
        assert captured.out.splitlines()[-2:] == ["z.opaque", "a.opaque"]
    assert captured.err == ""


@pytest.mark.parametrize("stage", ["construct", "observe"])
@pytest.mark.parametrize(
    "failure", [PermissionError("read denied"), OSError("file changed"), ValueError("unsafe path")]
)
def test_provider_failures_are_reported_unchanged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    stage: str,
    failure: Exception,
) -> None:
    constructor = Mock()
    if stage == "construct":
        constructor.side_effect = failure
    else:
        constructor.return_value.observe.side_effect = failure
    monkeypatch.setattr(cli, "LocalFilesystemReferenceProvider", constructor)

    assert main(["references", "scan-local", str(tmp_path), "--source-id", "local", "--json"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == f"artsniffer: error: {failure}\n"
    if stage == "construct":
        constructor.return_value.observe.assert_not_called()
    else:
        constructor.return_value.observe.assert_called_once_with()


@pytest.mark.parametrize("stage", ["construct", "observe"])
@pytest.mark.parametrize("failure", [RuntimeError("bug"), TypeError("bug"), AssertionError("bug")])
def test_unexpected_errors_propagate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    stage: str,
    failure: Exception,
) -> None:
    constructor = Mock()
    if stage == "construct":
        constructor.side_effect = failure
    else:
        constructor.return_value.observe.side_effect = failure
    monkeypatch.setattr(cli, "LocalFilesystemReferenceProvider", constructor)

    with pytest.raises(type(failure)) as error:
        main(["references", "scan-local", str(tmp_path), "--source-id", "local"])
    assert error.value is failure
    captured = capsys.readouterr()
    assert captured.out == captured.err == ""


def test_cli_has_only_agreed_dependencies() -> None:
    module_path = Path(__file__).resolve().parents[1] / "src" / "artsniffer" / "cli.py"
    allowed = {
        "argparse",
        "json",
        "sys",
        "collections.abc",
        "pathlib",
        "artsniffer.references.local_filesystem",
    }
    for node in ast.walk(ast.parse(module_path.read_text(encoding="utf-8"))):
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
