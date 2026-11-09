"""Synthetic CLI tests for managed local reference refresh."""

import hashlib
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from artsniffer import main
from artsniffer.commands import refresh_local
from artsniffer.commands.snapshot_file import read_snapshot
from artsniffer.references.observation import ReferenceItemObservation


def digest(content: bytes) -> str:
    return f"sha256:{hashlib.sha256(content).hexdigest()}"


def observation(item_id: str, content: bytes = b"same", source_id: str = "local"):
    return ReferenceItemObservation(source_id, item_id, digest(content))


def snapshot_item(item_id: str, content: bytes = b"same") -> dict[str, str]:
    return {"source_item_id": item_id, "content_hash": digest(content)}


def save_state(
    path: Path,
    items: list[dict[str, str]],
    *,
    source_id: str = "local",
    root: str = "historical root",
    versioned: bool = True,
    bom: bool = False,
) -> None:
    value: dict[str, object] = {
        "source_id": source_id,
        "root": root,
        "item_count": len(items),
        "items": items,
    }
    if versioned:
        value["schema_version"] = 1
    content = json.dumps(value).encode("utf-8")
    path.write_bytes((b"\xef\xbb\xbf" if bom else b"") + content)


def refresh_argv(
    root: Path, state: Path, *, dry_run: bool = False, as_json: bool = True
) -> list[str]:
    return [
        "references",
        "refresh-local",
        str(root),
        "--source-id",
        "local",
        "--state",
        str(state),
        *(["--dry-run"] if dry_run else []),
        *(["--json"] if as_json else []),
    ]


def set_provider(monkeypatch, items, *, failure: Exception | None = None):
    provider = Mock(spec=["observe"])
    if failure is not None:
        provider.observe.side_effect = failure
    else:
        provider.observe.return_value = items
    constructor = Mock(return_value=provider)
    monkeypatch.setattr(refresh_local, "LocalFilesystemReferenceProvider", constructor)
    return constructor, provider


@pytest.mark.parametrize("dry_run", [False, True])
def test_missing_state_is_empty_and_scanned_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys, dry_run: bool
) -> None:
    root = tmp_path / "library with spaces"
    root.mkdir()
    state = tmp_path / "managed state" / "snapshot.json"
    state.parent.mkdir()
    current = (observation("z"), observation("a"))
    constructor, provider = set_provider(monkeypatch, current)

    result = main(refresh_argv(root, state, dry_run=dry_run))

    assert result == 0
    constructor.assert_called_once_with(source_id="local", root=root)
    provider.observe.assert_called_once_with()
    output = json.loads(capsys.readouterr().out)
    assert output == {
        "command": "refresh-local",
        "source_id": "local",
        "root": str(root),
        "state": str(state),
        "state_previously_existed": False,
        "dry_run": dry_run,
        "state_written": not dry_run,
        "resulting_item_count": 2,
        "counts": {"added": 2, "changed": 0, "unchanged": 0, "removed": 0},
        "changes": [
            {
                "kind": "added",
                "source_item_id": "z",
                "previous_content_hash": None,
                "current_content_hash": digest(b"same"),
            },
            {
                "kind": "added",
                "source_item_id": "a",
                "previous_content_hash": None,
                "current_content_hash": digest(b"same"),
            },
        ],
    }
    if dry_run:
        assert not state.exists()
    else:
        saved = read_snapshot(state)
        assert saved.schema_version == 1
        assert saved.root == str(root)
        assert [item.source_item_id for item in saved.items] == ["a", "z"]


def test_unchanged_legacy_bom_state_is_rewritten_as_version_1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    root = tmp_path / "library"
    root.mkdir()
    state = tmp_path / "state.json"
    save_state(state, [snapshot_item("unchanged")], versioned=False, bom=True)
    original = state.read_bytes()
    set_provider(monkeypatch, (observation("unchanged"),))

    result = main(refresh_argv(root, state))

    assert result == 0
    output = json.loads(capsys.readouterr().out)
    assert output["state_previously_existed"] is True
    assert output["state_written"] is True
    assert output["counts"] == {"added": 0, "changed": 0, "unchanged": 1, "removed": 0}
    assert state.read_bytes() != original
    assert read_snapshot(state).schema_version == 1


def test_empty_live_library_creates_empty_version_1_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    root = tmp_path / "empty library"
    root.mkdir()
    state = tmp_path / "state.json"
    set_provider(monkeypatch, ())

    result = main(refresh_argv(root, state))

    assert result == 0
    output = json.loads(capsys.readouterr().out)
    assert output["resulting_item_count"] == 0
    assert output["counts"] == {"added": 0, "changed": 0, "unchanged": 0, "removed": 0}
    assert read_snapshot(state).items == ()


def test_mixed_refresh_reports_order_and_writes_complete_current_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    root = tmp_path / "library"
    root.mkdir()
    state = tmp_path / "state.json"
    save_state(
        state,
        [
            snapshot_item("z-removed"),
            snapshot_item("unchanged"),
            snapshot_item("changed"),
            snapshot_item("a-removed"),
        ],
    )
    current = (
        observation("z-added"),
        observation("changed", b"new"),
        observation("unchanged"),
    )
    set_provider(monkeypatch, current)

    result = main(refresh_argv(root, state))

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
    assert [item.source_item_id for item in read_snapshot(state).items] == [
        "changed",
        "unchanged",
        "z-added",
    ]


def test_dry_run_preserves_existing_state_bytes(tmp_path: Path, monkeypatch, capsys) -> None:
    root = tmp_path / "library"
    root.mkdir()
    state = tmp_path / "state.json"
    save_state(state, [snapshot_item("old")])
    original = state.read_bytes()
    set_provider(monkeypatch, (observation("new"),))

    result = main(refresh_argv(root, state, dry_run=True))

    assert result == 0
    output = json.loads(capsys.readouterr().out)
    assert output["dry_run"] is True
    assert output["state_written"] is False
    assert state.read_bytes() == original


@pytest.mark.parametrize("failure", ["malformed", "source-mismatch"])
def test_state_validation_failure_happens_before_provider_construction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys, failure: str
) -> None:
    root = tmp_path / "library"
    root.mkdir()
    state = tmp_path / "state.json"
    if failure == "malformed":
        state.write_text("{", encoding="utf-8")
    else:
        save_state(state, [], source_id="other")
    constructor = Mock()
    monkeypatch.setattr(refresh_local, "LocalFilesystemReferenceProvider", constructor)

    result = main(refresh_argv(root, state))

    assert result == 1
    constructor.assert_not_called()
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "artsniffer: error:" in captured.err


@pytest.mark.parametrize("stage", ["construct", "observe"])
@pytest.mark.parametrize(
    "failure", [OSError("read failed"), PermissionError("denied"), ValueError("provider failed")]
)
def test_provider_failure_preserves_existing_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys, stage: str, failure: Exception
) -> None:
    root = tmp_path / "library"
    root.mkdir()
    state = tmp_path / "state.json"
    save_state(state, [snapshot_item("old")])
    original = state.read_bytes()
    provider = Mock(spec=["observe"])
    provider.observe.side_effect = failure
    constructor = Mock(return_value=provider)
    if stage == "construct":
        constructor.side_effect = failure
    monkeypatch.setattr(refresh_local, "LocalFilesystemReferenceProvider", constructor)

    result = main(refresh_argv(root, state))

    assert result == 1
    assert state.read_bytes() == original
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == f"artsniffer: error: {failure}\n"
    if stage == "construct":
        provider.observe.assert_not_called()
    else:
        provider.observe.assert_called_once_with()


@pytest.mark.parametrize("stage", ["encoding", "writing"])
def test_refresh_encoding_or_write_failure_preserves_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys, stage: str
) -> None:
    root = tmp_path / "library"
    root.mkdir()
    state = tmp_path / "state.json"
    save_state(state, [snapshot_item("old")])
    original = state.read_bytes()
    content_hash = "invalid" if stage == "encoding" else digest(b"new")
    set_provider(monkeypatch, (ReferenceItemObservation("local", "new", content_hash),))
    if stage == "writing":
        monkeypatch.setattr(
            refresh_local,
            "safe_write",
            Mock(side_effect=PermissionError("write denied")),
        )

    result = main(refresh_argv(root, state))

    assert result == 1
    assert state.read_bytes() == original
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "artsniffer: error:" in captured.err


def test_refresh_never_writes_state_inside_reference_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    root = tmp_path / "library"
    root.mkdir()
    state = root / "state.json"
    constructor = Mock()
    safe_writer = Mock()
    monkeypatch.setattr(refresh_local, "LocalFilesystemReferenceProvider", constructor)
    monkeypatch.setattr(refresh_local, "safe_write", safe_writer)

    result = main(refresh_argv(root, state))

    assert result == 1
    constructor.assert_not_called()
    safe_writer.assert_not_called()
    assert not state.exists()
    assert list(root.iterdir()) == []
    assert capsys.readouterr().out == ""


def test_refresh_rejects_state_with_parent_inside_reference_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    root = tmp_path / "library with spaces"
    root.mkdir()
    state = root / ".."
    constructor = Mock()
    safe_writer = Mock()
    monkeypatch.setattr(refresh_local, "LocalFilesystemReferenceProvider", constructor)
    monkeypatch.setattr(refresh_local, "safe_write", safe_writer)

    result = main(refresh_argv(root, state))

    assert result == 1
    constructor.assert_not_called()
    safe_writer.assert_not_called()
    assert list(root.iterdir()) == []
    assert "must be outside the reference root" in capsys.readouterr().err


def test_refresh_human_output_states_source_paths_status_and_counts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    root = tmp_path / "library"
    root.mkdir()
    state = tmp_path / "state.json"
    set_provider(monkeypatch, (observation("added"),))

    result = main(refresh_argv(root, state, as_json=False))

    assert result == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == (
        f"Source: local\nRoot: {root}\nState: {state}\nStatus: State updated\n"
        "Added: 1\n  added\nChanged: 0\nUnchanged: 0\nRemoved: 0\n"
    )


def test_unexpected_refresh_errors_propagate(tmp_path: Path, monkeypatch, capsys) -> None:
    root = tmp_path / "library"
    root.mkdir()
    state = tmp_path / "state.json"
    constructor, provider = set_provider(monkeypatch, ())
    failure = RuntimeError("bug")
    provider.observe.side_effect = failure

    with pytest.raises(RuntimeError) as error:
        main(refresh_argv(root, state))

    assert error.value is failure
    assert constructor.call_count == 1
    captured = capsys.readouterr()
    assert captured.out == captured.err == ""
