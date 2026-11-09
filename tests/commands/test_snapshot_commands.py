"""Synthetic CLI tests for local snapshot management commands."""

import hashlib
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from artsniffer import main
from artsniffer.commands import snapshot_commands
from artsniffer.commands.snapshot_file import read_snapshot
from artsniffer.references.observation import ReferenceItemObservation


def digest(content: bytes) -> str:
    return f"sha256:{hashlib.sha256(content).hexdigest()}"


def item(source_item_id: str, content: bytes = b"same") -> dict[str, str]:
    return {"source_item_id": source_item_id, "content_hash": digest(content)}


def save_snapshot(
    path: Path,
    items: list[dict[str, str]],
    *,
    source_id: str = "local",
    root: str = "historical root",
    versioned: bool = True,
) -> Path:
    value: dict[str, object] = {
        "source_id": source_id,
        "root": root,
        "item_count": len(items),
        "items": items,
    }
    if versioned:
        value["schema_version"] = 1
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def snapshot_argv(*parts: str, as_json: bool = False) -> list[str]:
    return [
        "references",
        "snapshot",
        *parts,
        *(["--json"] if as_json else []),
    ]


@pytest.mark.parametrize("as_json", [False, True])
def test_snapshot_create_saves_version_1_once_and_separates_result_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys, as_json: bool
) -> None:
    root = tmp_path / "library with spaces"
    root.mkdir()
    output = tmp_path / "saved snapshots" / "reference.json"
    output.parent.mkdir()
    items = (
        ReferenceItemObservation(" exact source ", "z.opaque", digest(b"z")),
        ReferenceItemObservation(" exact source ", "../opaque", digest(b"opaque")),
    )
    provider = Mock(spec=["observe"])
    provider.observe.return_value = items
    constructor = Mock(return_value=provider)
    monkeypatch.setattr(snapshot_commands, "LocalFilesystemReferenceProvider", constructor)
    argv = snapshot_argv(
        "create",
        str(root),
        "--source-id",
        " exact source ",
        "--output",
        str(output),
        as_json=as_json,
    )

    assert main(argv) == 0

    constructor.assert_called_once_with(source_id=" exact source ", root=root)
    provider.observe.assert_called_once_with()
    saved = read_snapshot(output)
    assert saved.schema_version == 1
    assert saved.source_id == " exact source "
    assert saved.root == str(root)
    assert [observation.source_item_id for observation in saved.items] == ["../opaque", "z.opaque"]
    captured = capsys.readouterr()
    assert captured.err == ""
    if as_json:
        assert json.loads(captured.out) == {
            "command": "snapshot create",
            "source_id": " exact source ",
            "root": str(root),
            "output": str(output),
            "item_count": 2,
            "written": True,
        }
        assert "items" not in json.loads(captured.out)
    else:
        assert captured.out == (
            f"Created snapshot: {output}\n"
            "Source:  exact source \n"
            f"Root: {root}\n"
            "Observed reference items: 2\n"
        )


def test_snapshot_create_refuses_existing_target_before_provider_construction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    root = tmp_path / "library"
    root.mkdir()
    output = tmp_path / "snapshot.json"
    output.write_bytes(b"old bytes")
    constructor = Mock()
    monkeypatch.setattr(snapshot_commands, "LocalFilesystemReferenceProvider", constructor)

    result = main(
        snapshot_argv(
            "create", str(root), "--source-id", "local", "--output", str(output), as_json=True
        )
    )

    assert result == 1
    constructor.assert_not_called()
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Snapshot already exists" in captured.err
    assert output.read_bytes() == b"old bytes"


def test_snapshot_create_never_writes_inside_reference_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    root = tmp_path / "library"
    root.mkdir()
    output = root / "managed snapshot.json"
    constructor = Mock()
    monkeypatch.setattr(snapshot_commands, "LocalFilesystemReferenceProvider", constructor)

    result = main(
        snapshot_argv(
            "create", str(root), "--source-id", "local", "--output", str(output), "--force"
        )
    )

    assert result == 1
    constructor.assert_not_called()
    assert not output.exists()
    assert capsys.readouterr().out == ""


def test_snapshot_create_force_replaces_existing_target(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = tmp_path / "library"
    root.mkdir()
    output = tmp_path / "snapshot.json"
    output.write_bytes(b"old bytes")
    provider = Mock(spec=["observe"])
    provider.observe.return_value = (ReferenceItemObservation("local", "new", digest(b"new")),)
    monkeypatch.setattr(
        snapshot_commands,
        "LocalFilesystemReferenceProvider",
        Mock(return_value=provider),
    )

    result = main(
        snapshot_argv(
            "create",
            str(root),
            "--source-id",
            "local",
            "--output",
            str(output),
            "--force",
        )
    )

    assert result == 0
    assert read_snapshot(output).items == (
        ReferenceItemObservation("local", "new", digest(b"new")),
    )
    assert capsys.readouterr().err == ""


@pytest.mark.parametrize("failure", [OSError("scan failed"), ValueError("invalid result")])
def test_snapshot_create_failure_keeps_target_and_emits_no_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys, failure: Exception
) -> None:
    root = tmp_path / "library"
    root.mkdir()
    output = tmp_path / "snapshot.json"
    output.write_bytes(b"old bytes")
    provider = Mock(spec=["observe"])
    provider.observe.side_effect = failure
    monkeypatch.setattr(
        snapshot_commands,
        "LocalFilesystemReferenceProvider",
        Mock(return_value=provider),
    )

    result = main(
        snapshot_argv(
            "create",
            str(root),
            "--source-id",
            "local",
            "--output",
            str(output),
            "--force",
            as_json=True,
        )
    )

    assert result == 1
    assert output.read_bytes() == b"old bytes"
    captured = capsys.readouterr()
    assert captured.out == ""
    assert f"artsniffer: error: {failure}" == captured.err.strip()


@pytest.mark.parametrize("stage", ["encoding", "writing"])
def test_snapshot_create_encoding_or_write_failure_keeps_previous_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys, stage: str
) -> None:
    root = tmp_path / "library"
    root.mkdir()
    output = tmp_path / "snapshot.json"
    output.write_bytes(b"old bytes")
    content_hash = "invalid" if stage == "encoding" else digest(b"new")
    provider = Mock(spec=["observe"])
    provider.observe.return_value = (ReferenceItemObservation("local", "new", content_hash),)
    monkeypatch.setattr(
        snapshot_commands,
        "LocalFilesystemReferenceProvider",
        Mock(return_value=provider),
    )
    if stage == "writing":
        monkeypatch.setattr(
            snapshot_commands,
            "safe_write",
            Mock(side_effect=PermissionError("write denied")),
        )

    result = main(
        snapshot_argv(
            "create",
            str(root),
            "--source-id",
            "local",
            "--output",
            str(output),
            "--force",
            as_json=True,
        )
    )

    assert result == 1
    assert output.read_bytes() == b"old bytes"
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "artsniffer: error:" in captured.err


@pytest.mark.parametrize(
    ("versioned", "expected"), [(False, "legacy-unversioned"), (True, "version-1")]
)
@pytest.mark.parametrize("as_json", [False, True])
def test_snapshot_validate_reports_metadata_and_optional_exact_source(
    tmp_path: Path, capsys, versioned: bool, expected: str, as_json: bool
) -> None:
    path = save_snapshot(tmp_path / "snapshot.json", [item("opaque")], versioned=versioned)
    args = snapshot_argv(
        "validate",
        str(path),
        "--source-id",
        "local",
        as_json=as_json,
    )

    assert main(args) == 0

    captured = capsys.readouterr()
    assert captured.err == ""
    if as_json:
        assert json.loads(captured.out) == {
            "valid": True,
            "format": expected,
            "schema_version": 1 if versioned else None,
            "source_id": "local",
            "root": "historical root",
            "item_count": 1,
        }
    else:
        assert f"Schema version: {'1' if versioned else 'legacy (unversioned)'}" in captured.out
        assert "Source: local" in captured.out
        assert "Items: 1" in captured.out


def test_snapshot_validate_source_mismatch_fails_without_provider(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    path = save_snapshot(tmp_path / "snapshot.json", [])
    constructor = Mock()
    monkeypatch.setattr(snapshot_commands, "LocalFilesystemReferenceProvider", constructor)

    result = main(snapshot_argv("validate", str(path), "--source-id", "LOCAL", as_json=True))

    assert result == 1
    constructor.assert_not_called()
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "--source-id exactly" in captured.err


@pytest.mark.parametrize("as_json", [False, True])
def test_snapshot_show_lists_opaque_ids_only_when_requested(
    tmp_path: Path, capsys, as_json: bool
) -> None:
    ids = ["../not-a-path", " Item ", "item"]
    path = save_snapshot(tmp_path / "snapshot.json", [item(item_id) for item_id in ids])

    result = main(snapshot_argv("show", str(path), "--items", as_json=as_json))

    assert result == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert not (tmp_path / "not-a-path").exists()
    if as_json:
        output = json.loads(captured.out)
        assert [entry["source_item_id"] for entry in output["items"]] == ids
        assert all(entry["content_hash"] == digest(b"same") for entry in output["items"])
    else:
        assert captured.out.splitlines()[-3:] == ids


def test_snapshot_show_metadata_omits_item_ids_by_default(tmp_path: Path, capsys) -> None:
    path = save_snapshot(tmp_path / "snapshot.json", [item("opaque")])

    assert main(snapshot_argv("show", str(path), as_json=True)) == 0

    output = json.loads(capsys.readouterr().out)
    assert output["item_count"] == 1
    assert "items" not in output


def test_valid_read_only_snapshot_commands_never_construct_provider(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    previous = save_snapshot(tmp_path / "previous.json", [item("unchanged")])
    current = save_snapshot(tmp_path / "current.json", [item("unchanged")])
    constructor = Mock()
    monkeypatch.setattr(snapshot_commands, "LocalFilesystemReferenceProvider", constructor)

    for args in (
        snapshot_argv("validate", str(previous)),
        snapshot_argv("show", str(previous)),
        snapshot_argv("diff", str(previous), str(current)),
    ):
        assert main(args) == 0
        assert capsys.readouterr().err == ""

    constructor.assert_not_called()


def test_snapshot_validate_read_failure_returns_one_without_stdout(tmp_path: Path, capsys) -> None:
    path = tmp_path / "malformed.json"
    path.write_text("{", encoding="utf-8")

    result = main(snapshot_argv("validate", str(path), as_json=True))

    assert result == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "artsniffer: error: Snapshot" in captured.err


def test_snapshot_diff_preserves_current_order_and_sorts_removals(tmp_path: Path, capsys) -> None:
    previous = save_snapshot(
        tmp_path / "previous.json",
        [item("z-removed"), item("unchanged"), item("changed"), item("a-removed")],
    )
    current = save_snapshot(
        tmp_path / "current.json",
        [item("z-added"), item("changed", b"new"), item("unchanged")],
    )

    result = main(snapshot_argv("diff", str(previous), str(current), as_json=True))

    assert result == 0
    output = json.loads(capsys.readouterr().out)
    assert output["counts"] == {"added": 1, "changed": 1, "unchanged": 1, "removed": 2}
    assert [(change["kind"], change["source_item_id"]) for change in output["changes"]] == [
        ("added", "z-added"),
        ("changed", "changed"),
        ("unchanged", "unchanged"),
        ("removed", "a-removed"),
        ("removed", "z-removed"),
    ]
    assert output["changes"][0]["previous_content_hash"] is None
    assert output["changes"][0]["current_content_hash"] == digest(b"same")
    assert output["changes"][1]["previous_content_hash"] == digest(b"same")
    assert output["changes"][1]["current_content_hash"] == digest(b"new")
    assert output["changes"][-1]["previous_content_hash"] == digest(b"same")
    assert output["changes"][-1]["current_content_hash"] is None


def test_snapshot_diff_human_output_lists_changed_and_removed_ids(tmp_path: Path, capsys) -> None:
    previous = save_snapshot(tmp_path / "previous.json", [item("removed"), item("changed")])
    current = save_snapshot(tmp_path / "current.json", [item("changed", b"new"), item("added")])

    result = main(snapshot_argv("diff", str(previous), str(current)))

    assert result == 0
    output = capsys.readouterr().out
    assert "Added: 1\n  added" in output
    assert "Changed: 1\n  changed" in output
    assert "Removed: 1\n  removed" in output


def test_snapshot_diff_rejects_source_mismatch_without_provider(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    previous = save_snapshot(tmp_path / "previous.json", [], source_id="local")
    current = save_snapshot(tmp_path / "current.json", [], source_id="other")
    constructor = Mock()
    monkeypatch.setattr(snapshot_commands, "LocalFilesystemReferenceProvider", constructor)

    result = main(snapshot_argv("diff", str(previous), str(current)))

    assert result == 1
    constructor.assert_not_called()
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "source_id values must match exactly" in captured.err


def test_snapshot_usage_errors_return_two() -> None:
    with pytest.raises(SystemExit) as error:
        main(["references", "snapshot", "create", "ROOT"])

    assert error.value.code == 2
