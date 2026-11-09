"""Atomic publication and failure-recovery tests for snapshot/state files."""

from __future__ import annotations

import os
from pathlib import Path
from typing import IO, Any

import pytest

from artsniffer.commands import safe_write as writer


def task_temporaries(path: Path) -> list[Path]:
    return list(path.parent.glob(f".{path.name}.*.tmp"))


def test_safe_write_creates_complete_file_in_path_with_spaces(tmp_path: Path) -> None:
    target = tmp_path / "folder with spaces" / "state file.json"
    target.parent.mkdir()
    content = b'{"complete": true}\n'

    writer.safe_write(target, content, overwrite=False)

    assert target.read_bytes() == content
    assert task_temporaries(target) == []


def test_safe_write_replaces_existing_file_and_can_write_empty_content(tmp_path: Path) -> None:
    target = tmp_path / "snapshot.json"
    target.write_bytes(b"old")

    writer.safe_write(target, b"", overwrite=True)

    assert target.read_bytes() == b""
    assert task_temporaries(target) == []


def test_safe_write_refuses_existing_file_without_changing_it(tmp_path: Path) -> None:
    target = tmp_path / "snapshot.json"
    target.write_bytes(b"original")

    with pytest.raises(FileExistsError, match="File already exists"):
        writer.safe_write(target, b"replacement", overwrite=False)

    assert target.read_bytes() == b"original"
    assert task_temporaries(target) == []


def test_safe_write_does_not_replace_a_target_created_during_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "snapshot.json"
    unrelated = tmp_path / ".snapshot.json.unrelated.tmp"
    unrelated.write_bytes(b"leave alone")
    original_link = os.link

    def create_collision(source: str | os.PathLike[str], destination: str | os.PathLike[str]):
        Path(destination).write_bytes(b"racing writer")
        original_link(source, destination)

    monkeypatch.setattr(writer.os, "link", create_collision)

    with pytest.raises(FileExistsError):
        writer.safe_write(target, b"ours", overwrite=False)

    assert target.read_bytes() == b"racing writer"
    assert unrelated.read_bytes() == b"leave alone"
    assert task_temporaries(target) == [unrelated]


def test_safe_write_preserves_old_bytes_and_cleans_up_after_write_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "state.json"
    target.write_bytes(b"old state")
    real_fdopen = os.fdopen

    class FailingStream:
        def __init__(self, stream: IO[Any]) -> None:
            self._stream = stream

        def __enter__(self) -> FailingStream:
            return self

        def __exit__(self, *args: object) -> None:
            self._stream.close()

        def write(self, content: bytes) -> int:
            self._stream.write(content[:2])
            raise OSError("write failed")

        def flush(self) -> None:
            self._stream.flush()

    def failing_fdopen(descriptor: int, mode: str) -> FailingStream:
        return FailingStream(real_fdopen(descriptor, mode))

    monkeypatch.setattr(writer.os, "fdopen", failing_fdopen)

    with pytest.raises(OSError, match="write failed"):
        writer.safe_write(target, b"new state", overwrite=True)

    assert target.read_bytes() == b"old state"
    assert task_temporaries(target) == []


def test_safe_write_preserves_old_bytes_and_cleans_up_after_replace_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "state.json"
    target.write_bytes(b"old state")
    unrelated = tmp_path / ".state.json.unrelated.tmp"
    unrelated.write_bytes(b"leave alone")

    def fail_replace(source: str | os.PathLike[str], destination: str | os.PathLike[str]) -> None:
        assert Path(source).parent == Path(destination).parent
        assert Path(source).read_bytes() == b"new state"
        raise OSError("replace failed")

    monkeypatch.setattr(writer.os, "replace", fail_replace)

    with pytest.raises(OSError, match="replace failed"):
        writer.safe_write(target, b"new state", overwrite=True)

    assert target.read_bytes() == b"old state"
    assert unrelated.read_bytes() == b"leave alone"
    assert task_temporaries(target) == [unrelated]


def test_safe_write_repeated_content_is_deterministic(tmp_path: Path) -> None:
    target = tmp_path / "state.json"
    content = b'{"items":[],"schema_version":1}\n'

    writer.safe_write(target, content, overwrite=False)
    first = target.read_bytes()
    writer.safe_write(target, content, overwrite=True)

    assert target.read_bytes() == first == content
    assert task_temporaries(target) == []
