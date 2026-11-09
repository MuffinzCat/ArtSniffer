"""Synthetic baseline and CLI tests; never read personal reference libraries."""

import ast
import hashlib
import json
import os
from pathlib import Path
from unittest.mock import Mock

import pytest

from artsniffer import main
from artsniffer.commands import references
from artsniffer.references.observation import ReferenceItemObservation


def digest(content: bytes) -> str:
    return f"sha256:{hashlib.sha256(content).hexdigest()}"


def snapshot():
    return {
        "schema_version": 1,
        "source_id": "local",
        "root": "historical root that need not exist",
        "item_count": 1,
        "items": [{"source_item_id": "same.png", "content_hash": digest(b"same")}],
    }


def save_baseline(tmp_path: Path, value=None, encoding: str = "utf-8") -> Path:
    path = tmp_path / "baseline.json"
    path.write_text(json.dumps(snapshot() if value is None else value), encoding=encoding)
    return path


def argv(root: Path, baseline: Path, as_json: bool = False, source_id: str = "local") -> list[str]:
    return [
        "references",
        "diff-local",
        str(root),
        "--source-id",
        source_id,
        "--against",
        str(baseline),
        *(["--json"] if as_json else []),
    ]


def assert_baseline_failure(root, baseline, capsys, monkeypatch, message, as_json):
    constructor = Mock()
    monkeypatch.setattr(references, "LocalFilesystemReferenceProvider", constructor)
    assert main(argv(root, baseline, as_json)) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith(f"artsniffer: error: Baseline {baseline}: ")
    assert message in captured.err
    assert "Traceback" not in captured.err
    constructor.assert_not_called()


@pytest.mark.parametrize("as_json", [False, True])
@pytest.mark.parametrize(
    ("raw", "message"),
    [
        (b"{", "Expecting property name"),
        (b"{}", "Missing fields:"),
        (b"null", "Snapshot must be a JSON object."),
        (b"[]", "Snapshot must be a JSON object."),
        (b"true", "Snapshot must be a JSON object."),
        (b'{"source_id":"local","source_id":"local"}', "Duplicate JSON key: source_id."),
        (
            b'{"items":[{"content_hash":"a","content_hash":"b"}]}',
            "Duplicate JSON key: content_hash.",
        ),
        (b'{"x":{"a":1,"a":2}}', "Duplicate JSON key: a."),
        (b'{"x":NaN}', "Invalid JSON constant: NaN."),
        (b'{"x":Infinity}', "Invalid JSON constant: Infinity."),
        (b'{"x":-Infinity}', "Invalid JSON constant: -Infinity."),
        (b'{"x":1,}', "Expecting property name"),
        (b"{} trailing", "Extra data"),
        (b'{"root":"\xff"}', "codec can't decode byte"),
        (b"\xff\xfe{\x00}\x00", "codec can't decode byte"),
    ],
)
def test_invalid_json_never_scans(tmp_path, capsys, monkeypatch, raw, message, as_json):
    baseline = tmp_path / "baseline.json"
    baseline.write_bytes(raw)
    assert_baseline_failure(tmp_path, baseline, capsys, monkeypatch, message, as_json)


@pytest.mark.parametrize("as_json", [False, True])
@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("schema_version", 0, "schema_version must be integer 1 when present."),
        ("schema_version", 2, "schema_version must be integer 1 when present."),
        ("schema_version", True, "schema_version must be integer 1 when present."),
        ("schema_version", 1.0, "schema_version must be integer 1 when present."),
        ("schema_version", "1", "schema_version must be integer 1 when present."),
        ("schema_version", None, "schema_version must be integer 1 when present."),
        ("source_id", "", "source_id must be a non-blank string."),
        ("source_id", " \t", "source_id must be a non-blank string."),
        ("source_id", 1, "source_id must be a non-blank string."),
        ("source_id", None, "source_id must be a non-blank string."),
        ("source_id", "Local", "Baseline source_id must match --source-id exactly."),
        ("source_id", " local ", "Baseline source_id must match --source-id exactly."),
        ("root", "", "root must be a non-blank string."),
        ("root", "\t", "root must be a non-blank string."),
        ("root", {}, "root must be a non-blank string."),
        ("root", None, "root must be a non-blank string."),
        ("item_count", True, "item_count must be a non-negative integer."),
        ("item_count", -1, "item_count must be a non-negative integer."),
        ("item_count", 1.0, "item_count must be a non-negative integer."),
        ("item_count", "1", "item_count must be a non-negative integer."),
        ("item_count", None, "item_count must be a non-negative integer."),
        ("item_count", 0, "item_count must equal the number of items."),
        ("item_count", 2, "item_count must equal the number of items."),
        ("items", {}, "items must be an array."),
        ("items", None, "items must be an array."),
        ("items", "items", "items must be an array."),
        ("items", [], "item_count must equal the number of items."),
        ("extra", 1, "Unexpected fields: extra."),
    ],
)
def test_invalid_snapshot_fields_never_scan(
    tmp_path, capsys, monkeypatch, field, value, message, as_json
):
    data = snapshot()
    data[field] = value
    baseline = save_baseline(tmp_path, data)
    assert_baseline_failure(tmp_path, baseline, capsys, monkeypatch, message, as_json)


@pytest.mark.parametrize("field", ["source_id", "root", "item_count", "items"])
def test_missing_snapshot_fields(tmp_path, capsys, monkeypatch, field):
    data = snapshot()
    del data[field]
    baseline = save_baseline(tmp_path, data)
    assert_baseline_failure(
        tmp_path, baseline, capsys, monkeypatch, f"Missing fields: {field}.", True
    )


@pytest.mark.parametrize("as_json", [False, True])
@pytest.mark.parametrize(
    ("item", "message"),
    [
        (None, "Item must be a JSON object."),
        ([], "Item must be a JSON object."),
        ("item", "Item must be a JSON object."),
        ({}, "Missing fields: content_hash, source_item_id."),
        ({"source_item_id": "item"}, "Missing fields: content_hash."),
        ({"content_hash": digest(b"x")}, "Missing fields: source_item_id."),
        (
            {"source_item_id": "item", "content_hash": digest(b"x"), "source_id": "other"},
            "Unexpected fields: source_id.",
        ),
        (
            {"source_item_id": "item", "content_hash": digest(b"x"), "extra": 0},
            "Unexpected fields: extra.",
        ),
        ({"source_item_id": "", "content_hash": digest(b"x")}, "source_item_id must be"),
        ({"source_item_id": " \t", "content_hash": digest(b"x")}, "source_item_id must be"),
        ({"source_item_id": 1, "content_hash": digest(b"x")}, "source_item_id must be"),
        ({"source_item_id": None, "content_hash": digest(b"x")}, "source_item_id must be"),
        ({"source_item_id": "item", "content_hash": None}, "content_hash must be"),
        ({"source_item_id": "item", "content_hash": 1}, "content_hash must be"),
        ({"source_item_id": "item", "content_hash": ""}, "content_hash must be"),
        ({"source_item_id": "item", "content_hash": " \t"}, "content_hash must be"),
        ({"source_item_id": "item", "content_hash": "opaque"}, "content_hash must be"),
        ({"source_item_id": "item", "content_hash": "sha256:" + "a" * 63}, "content_hash must be"),
        ({"source_item_id": "item", "content_hash": "sha256:" + "a" * 65}, "content_hash must be"),
        ({"source_item_id": "item", "content_hash": "sha256:" + "A" * 64}, "content_hash must be"),
        ({"source_item_id": "item", "content_hash": "sha256:" + "g" * 64}, "content_hash must be"),
        ({"source_item_id": "item", "content_hash": "SHA256:" + "a" * 64}, "content_hash must be"),
        ({"source_item_id": "item", "content_hash": digest(b"x") + "\n"}, "content_hash must be"),
    ],
)
def test_invalid_items_never_scan(tmp_path, capsys, monkeypatch, item, message, as_json):
    data = snapshot()
    data["items"] = [item]
    baseline = save_baseline(tmp_path, data)
    assert_baseline_failure(
        tmp_path, baseline, capsys, monkeypatch, f"items[0]: {message}", as_json
    )


@pytest.mark.parametrize("same_hash", [False, True])
def test_duplicate_ids_rejected_even_with_equal_hash(tmp_path, capsys, monkeypatch, same_hash):
    data = snapshot()
    data["item_count"] = 2
    data["items"].append(
        {"source_item_id": "same.png", "content_hash": digest(b"same" if same_hash else b"other")}
    )
    baseline = save_baseline(tmp_path, data)
    assert_baseline_failure(
        tmp_path,
        baseline,
        capsys,
        monkeypatch,
        "items[1]: Duplicate source_item_id: same.png.",
        True,
    )


@pytest.mark.parametrize("failure", ["missing", "directory", "denied"])
def test_baseline_filesystem_failures(tmp_path, capsys, monkeypatch, failure):
    baseline = tmp_path / "baseline.json"
    if failure == "directory":
        baseline.mkdir()
    elif failure == "denied":
        baseline.write_text("{}", encoding="utf-8")
        monkeypatch.setattr(Path, "read_text", Mock(side_effect=PermissionError("read denied")))
    assert_baseline_failure(
        tmp_path,
        baseline,
        capsys,
        monkeypatch,
        "read denied" if failure == "denied" else str(baseline),
        True,
    )


@pytest.mark.parametrize("as_json", [False, True])
def test_reads_baseline_and_constructs_and_observes_once(tmp_path, capsys, monkeypatch, as_json):
    data = snapshot()
    data["source_id"] = " exact source "
    baseline = save_baseline(tmp_path, data)
    original_read = Path.read_text
    reads = []

    def read(self, *args, **kwargs):
        reads.append(self)
        return original_read(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read)
    provider = Mock(spec=["observe"])
    provider.observe.return_value = (
        ReferenceItemObservation(" exact source ", "z.opaque", "z"),
        ReferenceItemObservation(" exact source ", "a.opaque", "a"),
    )
    constructor = Mock(return_value=provider)
    monkeypatch.setattr(references, "LocalFilesystemReferenceProvider", constructor)

    assert main(argv(tmp_path, baseline, as_json, " exact source ")) == 0
    constructor.assert_called_once_with(source_id=" exact source ", root=tmp_path)
    provider.observe.assert_called_once_with()
    assert reads == [baseline]
    captured = capsys.readouterr()
    assert captured.err == ""
    if as_json:
        changes = json.loads(captured.out)["changes"]
        assert [change["source_item_id"] for change in changes] == [
            "z.opaque",
            "a.opaque",
            "same.png",
        ]
    else:
        assert "Added: 2\n  z.opaque\n  a.opaque\n" in captured.out


@pytest.mark.parametrize("as_json", [False, True])
@pytest.mark.parametrize("stage", ["construct", "observe"])
@pytest.mark.parametrize(
    "failure", [PermissionError("read denied"), OSError("file changed"), ValueError("unsafe path")]
)
def test_diff_provider_errors(tmp_path, capsys, monkeypatch, as_json, stage, failure):
    baseline = save_baseline(tmp_path)
    constructor = Mock()
    if stage == "construct":
        constructor.side_effect = failure
    else:
        constructor.return_value.observe.side_effect = failure
    monkeypatch.setattr(references, "LocalFilesystemReferenceProvider", constructor)
    assert main(argv(tmp_path, baseline, as_json)) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == f"artsniffer: error: {failure}\n"
    constructor.assert_called_once_with(source_id="local", root=tmp_path)
    if stage == "construct":
        constructor.return_value.observe.assert_not_called()
    else:
        constructor.return_value.observe.assert_called_once_with()


@pytest.mark.parametrize("failure", [RuntimeError("bug"), TypeError("bug"), AssertionError("bug")])
def test_diff_does_not_hide_unexpected_errors(tmp_path, capsys, monkeypatch, failure):
    baseline = save_baseline(tmp_path)
    constructor = Mock()
    constructor.return_value.observe.side_effect = failure
    monkeypatch.setattr(references, "LocalFilesystemReferenceProvider", constructor)
    with pytest.raises(type(failure)) as error:
        main(argv(tmp_path, baseline, True))
    assert error.value is failure
    captured = capsys.readouterr()
    assert captured.out == captured.err == ""


@pytest.mark.parametrize("as_json", [False, True])
@pytest.mark.parametrize("legacy", [False, True])
@pytest.mark.parametrize("encoding", ["utf-8", "utf-8-sig"])
def test_saved_scan_roundtrip_and_mixed_changes(tmp_path, capsys, as_json, legacy, encoding):
    root = tmp_path / "library with spaces"
    root.mkdir()
    for name in ("unchanged.png", "changed.png", "z-removed.png", "a-removed.png"):
        (root / name).write_bytes(b"same")
    assert main(["references", "scan-local", str(root), "--source-id", "local", "--json"]) == 0
    scan = capsys.readouterr()
    assert scan.err == ""
    data = json.loads(scan.out)
    assert data["schema_version"] == 1
    if legacy:
        del data["schema_version"]
    # Historical root metadata is not consulted or required to match the live root.
    data["root"] = "a historical directory that no longer exists"
    data["items"].reverse()
    baseline = save_baseline(tmp_path, data, encoding)
    (root / "changed.png").write_bytes(b"new")
    (root / "z-removed.png").unlink()
    (root / "a-removed.png").unlink()
    (root / "added.png").write_bytes(b"same")
    before = {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}

    assert main(argv(root, baseline, as_json)) == 0
    first = capsys.readouterr()
    assert main(argv(root, baseline, as_json)) == 0
    assert capsys.readouterr() == first
    assert first.err == ""
    assert {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()} == before
    if as_json:
        assert json.loads(first.out) == {
            "schema_version": 1,
            "source_id": "local",
            "root": str(root),
            "against": str(baseline),
            "counts": {"added": 1, "changed": 1, "unchanged": 1, "removed": 2},
            "changes": [
                {
                    "kind": kind,
                    "source_item_id": name,
                    "previous_content_hash": previous,
                    "current_content_hash": current,
                }
                for kind, name, previous, current in [
                    ("added", "added.png", None, digest(b"same")),
                    ("changed", "changed.png", digest(b"same"), digest(b"new")),
                    ("unchanged", "unchanged.png", digest(b"same"), digest(b"same")),
                    ("removed", "a-removed.png", digest(b"same"), None),
                    ("removed", "z-removed.png", digest(b"same"), None),
                ]
            ],
        }
    else:
        assert first.out == (
            f"Source: local\nRoot: {root}\nAgainst: {baseline}\n"
            "Added: 1\n  added.png\nChanged: 1\n  changed.png\n"
            "Unchanged: 1\nRemoved: 2\n  a-removed.png\n  z-removed.png\n"
        )


@pytest.mark.parametrize("count", [0, 18])
def test_exact_unchanged_category_counts(tmp_path, capsys, count):
    root = tmp_path / "library"
    root.mkdir()
    for index in range(count):
        (root / f"{index:02}.png").write_bytes(b"same")
    assert main(["references", "scan-local", str(root), "--source-id", "local", "--json"]) == 0
    baseline = save_baseline(tmp_path, json.loads(capsys.readouterr().out))
    assert main(argv(root, baseline)) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out.splitlines()[3:] == [
        "Added: 0",
        "Changed: 0",
        f"Unchanged: {count}",
        "Removed: 0",
    ]
    assert main(argv(root, baseline, True)) == 0
    captured = capsys.readouterr()
    assert json.loads(captured.out)["counts"] == {
        "added": 0,
        "changed": 0,
        "unchanged": count,
        "removed": 0,
    }
    assert len(json.loads(captured.out)["changes"]) == count


def test_baseline_ids_are_opaque_and_never_used_as_paths(tmp_path, capsys):
    data = snapshot()
    ids = ["../opaque.png", " Item ", "item", "ITEM", "\u00e9", "e\u0301"]
    data["items"] = [{"source_item_id": item, "content_hash": digest(b"x")} for item in ids]
    data["item_count"] = len(ids)
    baseline = save_baseline(tmp_path, data)
    root = tmp_path / "empty"
    root.mkdir()
    assert main(argv(root, baseline, True)) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert [change["source_item_id"] for change in json.loads(captured.out)["changes"]] == sorted(
        ids
    )


@pytest.mark.parametrize("failure", ["missing", "file"])
def test_diff_real_root_errors(tmp_path, capsys, failure):
    baseline = save_baseline(tmp_path)
    root = tmp_path / "invalid"
    if failure == "file":
        root.write_bytes(b"not a directory")
    assert main(argv(root, baseline, True)) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "artsniffer: error:" in captured.err
    assert (repr(str(root)) if failure == "missing" else str(root)) in captured.err
    assert "Traceback" not in captured.err


@pytest.mark.parametrize("as_json", [False, True])
def test_empty_scan(tmp_path: Path, capsys: pytest.CaptureFixture[str], as_json: bool) -> None:
    argv = ["references", "scan-local", str(tmp_path), "--source-id", "local"]
    assert main(argv + (["--json"] if as_json else [])) == 0
    captured = capsys.readouterr()
    if as_json:
        assert json.loads(captured.out) == {
            "schema_version": 1,
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
            "schema_version": 1,
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
    monkeypatch.setattr(references, "LocalFilesystemReferenceProvider", constructor)
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
    monkeypatch.setattr(references, "LocalFilesystemReferenceProvider", constructor)

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
    monkeypatch.setattr(references, "LocalFilesystemReferenceProvider", constructor)

    with pytest.raises(type(failure)) as error:
        main(["references", "scan-local", str(tmp_path), "--source-id", "local"])
    assert error.value is failure
    captured = capsys.readouterr()
    assert captured.out == captured.err == ""


def test_reference_commands_have_only_agreed_dependencies() -> None:
    allowed = {
        "argparse",
        "json",
        "re",
        "sys",
        "pathlib",
        "artsniffer.commands.snapshot_file",
        "artsniffer.commands.snapshot_commands",
        "artsniffer.commands.refresh_local",
        "artsniffer.references.local_filesystem",
        "artsniffer.references.observation",
        "artsniffer.references.snapshot_diff",
    }
    for node in ast.walk(ast.parse(Path(references.__file__).read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            assert all(alias.name in allowed for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            assert node.module in allowed
