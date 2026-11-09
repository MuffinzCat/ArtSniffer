"""Synthetic filesystem tests for local reference observations."""

import ast
import hashlib
import os
import subprocess
from pathlib import Path
from typing import BinaryIO
from unittest.mock import MagicMock

import pytest

from artsniffer.references.artwork import ArtworkRecord
from artsniffer.references.local_filesystem import LocalFilesystemReferenceProvider
from artsniffer.references.observation import (
    ReferenceItemChangeKind,
    ReferenceItemObservation,
    diff_reference_observations,
)
from artsniffer.references.provider import ReferenceProvider


def test_structural_provider_and_empty_snapshot(tmp_path: Path) -> None:
    provider: ReferenceProvider = LocalFilesystemReferenceProvider(" Source-A ", tmp_path)

    assert provider.source_id == " Source-A "
    assert provider.observe() == ()


@pytest.mark.parametrize("source_id", ["", " \t", None, 1])
def test_invalid_source_id(tmp_path: Path, source_id) -> None:
    with pytest.raises(ValueError) as error:
        LocalFilesystemReferenceProvider(source_id, tmp_path)
    assert str(error.value) == "Source ID must not be empty or whitespace."


@pytest.mark.parametrize("root", [None, 1, "library"])
def test_invalid_root_type(root) -> None:
    with pytest.raises(TypeError) as error:
        LocalFilesystemReferenceProvider("local", root)
    assert str(error.value) == "Reference root must be a Path."


def test_missing_root(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        LocalFilesystemReferenceProvider("local", tmp_path / "missing")


def test_non_directory_root(tmp_path: Path) -> None:
    root = tmp_path / "file.png"
    root.write_bytes(b"abc")
    with pytest.raises(NotADirectoryError):
        LocalFilesystemReferenceProvider("local", root)


@pytest.mark.parametrize(
    "suffix", [".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tif", ".tiff", ".JPG", ".WeBp"]
)
def test_supported_suffixes(tmp_path: Path, suffix: str) -> None:
    (tmp_path / f"image{suffix}").write_bytes(b"abc")
    provider = LocalFilesystemReferenceProvider("local", tmp_path)

    assert provider.observe() == (
        ReferenceItemObservation(
            "local",
            f"image{suffix}",
            "sha256:ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        ),
    )


def test_unsupported_files_are_not_opened(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("notes.txt", "vector.svg", "image.avif", "no-extension", "image.jpg.bak"):
        (tmp_path / name).write_bytes(b"not an image")

    def unexpected_open(*args, **kwargs):
        pytest.fail("Unsupported files must not be read.")

    monkeypatch.setattr(Path, "open", unexpected_open)
    assert LocalFilesystemReferenceProvider("local", tmp_path).observe() == ()


def test_nested_hidden_items_and_exact_sorted_ids(tmp_path: Path) -> None:
    names = (
        "z.png",
        "nested/same.png",
        ".hidden/.image.PNG",
        "folder.png/inner.jpg",
        "same.png",
        " Mixed Case \u00e9.PNG",
        ".private.gif",
        "benchmark-data/kept.webp",
    )
    for name in names:
        path = tmp_path.joinpath(*name.split("/"))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"same bytes")
    (tmp_path / ".gitignore").write_text("*", encoding="utf-8")
    provider = LocalFilesystemReferenceProvider(" exact source ", tmp_path)
    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))

    snapshot = provider.observe()

    assert isinstance(snapshot, tuple)
    assert tuple(item.source_item_id for item in snapshot) == tuple(sorted(names))
    assert all(item.source_id == " exact source " for item in snapshot)
    assert len({item.content_hash for item in snapshot}) == 1
    assert provider.observe() == snapshot
    assert sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*")) == before
    assert all(tmp_path.joinpath(*name.split("/")).read_bytes() == b"same bytes" for name in names)


@pytest.mark.parametrize("names", [("A.png", "a.png"), ("\u00e9.png", "e\u0301.png")])
def test_distinct_filename_spellings_are_not_normalised(tmp_path: Path, names) -> None:
    first, second = (tmp_path / name for name in names)
    first.write_bytes(b"one")
    if second.exists():
        pytest.skip("Filesystem aliases these filename spellings.")
    second.write_bytes(b"two")
    actual_names = {path.name for path in tmp_path.iterdir()}
    if actual_names != set(names):
        pytest.skip("Filesystem does not preserve these filename spellings.")

    snapshot = LocalFilesystemReferenceProvider("local", tmp_path).observe()

    assert tuple(item.source_item_id for item in snapshot) == tuple(sorted(names))


@pytest.mark.skipif(os.name == "nt", reason="Windows does not permit backslashes in filenames.")
def test_literal_backslash_in_posix_filename_is_preserved(tmp_path: Path) -> None:
    (tmp_path / "a\\b.png").write_bytes(b"abc")
    assert LocalFilesystemReferenceProvider("local", tmp_path).observe()[0].source_item_id == (
        "a\\b.png"
    )


@pytest.mark.parametrize(
    ("content", "digest"),
    [
        (b"", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
        (b"abc", "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"),
    ],
)
def test_known_hashes(tmp_path: Path, content: bytes, digest: str) -> None:
    (tmp_path / "image.png").write_bytes(content)
    assert LocalFilesystemReferenceProvider("local", tmp_path).observe()[0].content_hash == (
        f"sha256:{digest}"
    )


def test_hashing_uses_bounded_binary_reads(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    content = b"abc" * (1024 * 1024)
    path = tmp_path / "large.png"
    path.write_bytes(content)
    original_open = Path.open
    read_sizes: list[int] = []

    def tracked_open(self: Path, mode: str) -> BinaryIO:
        assert mode == "rb"
        stream = original_open(self, mode)
        wrapped = MagicMock(wraps=stream)
        wrapped.__enter__.return_value = wrapped
        wrapped.__exit__.side_effect = lambda *args: stream.close()

        def read(size: int) -> bytes:
            read_sizes.append(size)
            return stream.read(size)

        wrapped.read.side_effect = read
        return wrapped

    monkeypatch.setattr(Path, "open", tracked_open)
    snapshot = LocalFilesystemReferenceProvider("local", tmp_path).observe()

    assert snapshot[0].content_hash == f"sha256:{hashlib.sha256(content).hexdigest()}"
    assert len(read_sizes) > 2
    assert all(0 < size <= 1024 * 1024 for size in read_sizes)


def test_hash_depends_on_bytes_not_timestamps(tmp_path: Path) -> None:
    path = tmp_path / "image.png"
    path.write_bytes(b"abc")
    provider = LocalFilesystemReferenceProvider("local", tmp_path)
    first = provider.observe()
    original = path.stat()
    path.write_bytes(b"xyz")
    os.utime(path, ns=(original.st_atime_ns, original.st_mtime_ns))

    changed = provider.observe()

    assert changed[0].content_hash != first[0].content_hash
    os.utime(path, ns=(original.st_atime_ns, original.st_mtime_ns + 10_000_000_000))
    assert provider.observe() == changed


def test_differing_handle_ctime_does_not_imply_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "image.png").write_bytes(b"abc")
    provider = LocalFilesystemReferenceProvider("local", tmp_path)
    expected = provider.observe()
    original_fstat = os.fstat

    def different_ctime(fd: int) -> os.stat_result:
        metadata = original_fstat(fd)
        return os.stat_result(
            metadata,
            {
                "st_mtime_ns": metadata.st_mtime_ns,
                "st_ctime_ns": metadata.st_ctime_ns + 10_000_000,
            },
        )

    monkeypatch.setattr(os, "fstat", different_ctime)
    assert provider.observe() == expected


def test_relative_root_is_bound_before_chdir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "library"
    root.mkdir()
    (root / "image.png").write_bytes(b"abc")
    monkeypatch.chdir(tmp_path)
    provider = LocalFilesystemReferenceProvider("local", Path("library"))
    expected = provider.observe()
    monkeypatch.chdir(root)

    assert provider.observe() == expected


@pytest.mark.parametrize("replacement", ["missing", "file"])
def test_observe_revalidates_root(tmp_path: Path, replacement: str) -> None:
    root = tmp_path / "library"
    root.mkdir()
    provider = LocalFilesystemReferenceProvider("local", root)
    root.rmdir()
    if replacement == "file":
        root.write_bytes(b"abc")

    with pytest.raises(FileNotFoundError if replacement == "missing" else NotADirectoryError):
        provider.observe()


def make_symlink(link: Path, target: Path, directory: bool = False) -> None:
    try:
        link.symlink_to(target, target_is_directory=directory)
    except (OSError, NotImplementedError) as error:
        pytest.skip(f"Symlink creation unavailable: {error}")


@pytest.mark.parametrize("kind", ["file", "internal-file", "directory", "broken", "cycle"])
def test_encountered_symlinks_abort(tmp_path: Path, kind: str) -> None:
    root = tmp_path / "library"
    root.mkdir()
    target = tmp_path / "outside.png"
    target.write_bytes(b"abc")
    if kind == "internal-file":
        target = root / "image.png"
        target.write_bytes(b"abc")
    elif kind == "directory":
        target = tmp_path
    elif kind == "broken":
        target = tmp_path / "missing"
    elif kind == "cycle":
        target = root
    make_symlink(root / "link", target, kind in {"directory", "cycle"})

    with pytest.raises(ValueError, match="must not be a symlink or junction"):
        LocalFilesystemReferenceProvider("local", root).observe()


def test_symlink_root_is_rejected_at_construction(tmp_path: Path) -> None:
    root = tmp_path / "link"
    make_symlink(root, tmp_path, directory=True)
    with pytest.raises(ValueError, match="must not be a symlink or junction"):
        LocalFilesystemReferenceProvider("local", root)


def test_root_becoming_symlink_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "library"
    root.mkdir()
    provider = LocalFilesystemReferenceProvider("local", root)
    root.rmdir()
    make_symlink(root, tmp_path, directory=True)
    with pytest.raises(ValueError, match="must not be a symlink or junction"):
        provider.observe()


@pytest.mark.skipif(os.name != "nt", reason="Windows junction creation requires Windows.")
@pytest.mark.parametrize("at_root", [True, False])
def test_windows_junction_is_rejected(tmp_path: Path, at_root: bool) -> None:
    root = tmp_path / "library"
    target = tmp_path / "target"
    target.mkdir()
    if not at_root:
        root.mkdir()
    link = root if at_root else root / "junction"
    result = subprocess.run(
        [os.environ["COMSPEC"], "/c", "mklink", "/J", str(link), str(target)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        pytest.skip(f"Junction creation unavailable: {result.stderr.strip()}")
    try:
        assert link.is_junction()
        with pytest.raises(ValueError, match="must not be a symlink or junction"):
            provider = LocalFilesystemReferenceProvider("local", root)
            provider.observe()
    finally:
        link.rmdir()


def test_portable_junction_check(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "image.png"
    path.write_bytes(b"abc")
    provider = LocalFilesystemReferenceProvider("local", tmp_path)
    monkeypatch.setattr(Path, "is_junction", lambda self: self == path)
    with pytest.raises(ValueError, match="must not be a symlink or junction"):
        provider.observe()


@pytest.mark.parametrize("failure", ["read", "traversal", "disappearing"])
def test_native_failure_aborts_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    path = tmp_path / "image.png"
    path.write_bytes(b"abc")
    provider = LocalFilesystemReferenceProvider("local", tmp_path)
    error = FileNotFoundError("disappeared") if failure == "disappearing" else PermissionError("no")

    def fail(*args, **kwargs):
        raise error

    if failure == "traversal":
        monkeypatch.setattr(os, "scandir", fail)
    else:
        monkeypatch.setattr(Path, "open", fail)
    with pytest.raises(type(error)) as raised:
        provider.observe()
    assert raised.value is error


def test_read_failure_after_success_aborts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("one.png", "two.png"):
        (tmp_path / name).write_bytes(b"abc")
    original_open = Path.open
    calls = 0
    error = PermissionError("second read failed")

    def fail_second(self: Path, mode: str):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise error
        return original_open(self, mode)

    monkeypatch.setattr(Path, "open", fail_second)
    with pytest.raises(PermissionError) as raised:
        LocalFilesystemReferenceProvider("local", tmp_path).observe()
    assert raised.value is error
    assert calls == 2


@pytest.mark.parametrize("change", ["mutation", "replacement", "type"])
def test_changes_during_read_abort(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    path = tmp_path / "image.png"
    path.write_bytes(b"abc")
    original_open = Path.open
    original_fstat = os.fstat
    original_lstat = Path.lstat
    calls = 0
    path_checks = 0

    def change_after_read(fd: int):
        nonlocal calls
        calls += 1
        if calls == 2 and change == "mutation":
            with original_open(path, "ab") as stream:
                stream.write(b"more")
        return original_fstat(fd)

    def change_after_close(self: Path):
        nonlocal path_checks
        if self == path:
            path_checks += 1
            if path_checks == 2 and change != "mutation":
                path.unlink()
                if change == "replacement":
                    path.write_bytes(b"replacement")
                else:
                    path.mkdir()
        return original_lstat(self)

    monkeypatch.setattr(os, "fstat", change_after_read)
    monkeypatch.setattr(Path, "lstat", change_after_close)
    with pytest.raises(OSError, match="Reference file changed during observation"):
        LocalFilesystemReferenceProvider("local", tmp_path).observe()


def test_containment_uses_path_boundaries(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "library"
    root.mkdir()
    path = root / "image.png"
    path.write_bytes(b"abc")
    outside = tmp_path / "library-other" / "image.png"
    provider = LocalFilesystemReferenceProvider("local", root)
    original_resolve = Path.resolve
    monkeypatch.setattr(
        Path,
        "resolve",
        lambda self, strict=False: outside if self == path else original_resolve(self, strict),
    )

    with pytest.raises(ValueError, match="outside the configured root"):
        provider.observe()


def test_duplicate_ids_abort(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "image.png").write_bytes(b"abc")
    original_scandir = os.scandir
    with original_scandir(tmp_path) as entries:
        entry = next(entries)
    repeated = MagicMock()
    repeated.__enter__.return_value = iter((entry, entry))
    monkeypatch.setattr(os, "scandir", lambda path: repeated)

    with pytest.raises(ValueError) as error:
        LocalFilesystemReferenceProvider("local", tmp_path).observe()
    assert str(error.value) == "Duplicate observation for source item ID: image.png."


def test_snapshot_integrates_with_diff(tmp_path: Path) -> None:
    for name in ("unchanged.png", "changed.png", "removed.png", "old.png"):
        (tmp_path / name).write_bytes(b"original")
    provider = LocalFilesystemReferenceProvider("local", tmp_path)
    known = [
        ArtworkRecord(
            f"art-{item.source_item_id}", item.source_id, item.source_item_id, item.content_hash
        )
        for item in provider.observe()
    ]
    (tmp_path / "changed.png").write_bytes(b"changed")
    (tmp_path / "removed.png").unlink()
    (tmp_path / "old.png").rename(tmp_path / "renamed.png")
    (tmp_path / "added.png").write_bytes(b"new")

    changes = diff_reference_observations(provider.source_id, known, provider.observe())

    assert [(change.source_item_id, change.kind) for change in changes] == [
        ("added.png", ReferenceItemChangeKind.ADDED),
        ("changed.png", ReferenceItemChangeKind.CHANGED),
        ("renamed.png", ReferenceItemChangeKind.ADDED),
        ("unchanged.png", ReferenceItemChangeKind.UNCHANGED),
        ("old.png", ReferenceItemChangeKind.REMOVED),
        ("removed.png", ReferenceItemChangeKind.REMOVED),
    ]


def test_adapter_has_only_standard_library_and_observation_dependencies() -> None:
    path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "artsniffer"
        / "references"
        / "local_filesystem.py"
    )
    allowed = {"hashlib", "os", "stat", "pathlib", "artsniffer.references.observation"}
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            assert all(alias.name in allowed for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            assert node.module in allowed
