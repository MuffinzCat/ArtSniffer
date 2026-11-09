"""Read-only local reference observations for operator-controlled directory trees."""

import hashlib
import os
import stat
from pathlib import Path

from artsniffer.references.observation import ReferenceItemObservation

_IMAGE_SUFFIXES = frozenset({".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tif", ".tiff"})
_HASH_CHUNK_SIZE = 1024 * 1024


def _unlinked_stat(path: Path) -> os.stat_result:
    metadata = path.lstat()
    if stat.S_ISLNK(metadata.st_mode) or path.is_junction():
        raise ValueError(f"Reference path must not be a symlink or junction: {path}.")
    return metadata


def _file_state(metadata: os.stat_result) -> tuple[int, int, int, int, int]:
    # Windows path and handle APIs can report different ctime values for the same file.
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_size,
        metadata.st_mtime_ns,
    )


class LocalFilesystemReferenceProvider:
    """Observe supported files recursively, including hidden entries, without copying them.

    The tree must be operator-controlled and reasonably quiescent. Detected failures and file
    changes abort the entire snapshot; portable checks do not provide atomic snapshots or
    hostile-race-resistant confinement. Extensions select files, not image validity or safety.
    """

    def __init__(self, source_id: str, root: Path) -> None:
        """Bind an exact source identity and a strict canonical absolute directory."""
        if not isinstance(source_id, str) or not source_id.strip():
            raise ValueError("Source ID must not be empty or whitespace.")
        if not isinstance(root, Path):
            raise TypeError("Reference root must be a Path.")
        metadata = _unlinked_stat(root)
        if not stat.S_ISDIR(metadata.st_mode):
            raise NotADirectoryError(f"Reference root must be a directory: {root}.")
        self.source_id = source_id
        self._root = root.resolve(strict=True)
        self._root_identity = (metadata.st_dev, metadata.st_ino)
        self._validate_root()

    def _checked_stat(self, path: Path) -> os.stat_result:
        metadata = _unlinked_stat(path)
        resolved = path.resolve(strict=True)
        if not resolved.is_relative_to(self._root):
            raise ValueError(f"Reference path is outside the configured root: {path}.")
        if resolved != path:
            raise ValueError(f"Reference path changed during observation: {path}.")
        return metadata

    def _validate_root(self) -> None:
        metadata = self._checked_stat(self._root)
        if not stat.S_ISDIR(metadata.st_mode):
            raise NotADirectoryError(f"Reference root must be a directory: {self._root}.")
        if (metadata.st_dev, metadata.st_ino) != self._root_identity:
            raise OSError(f"Reference root changed during observation: {self._root}.")

    def _content_hash(self, path: Path, expected: os.stat_result) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as image_file:
            opened = os.fstat(image_file.fileno())
            if not stat.S_ISREG(opened.st_mode) or _file_state(opened) != _file_state(expected):
                raise OSError(f"Reference file changed during observation: {path}.")
            while chunk := image_file.read(_HASH_CHUNK_SIZE):
                digest.update(chunk)
            after = os.fstat(image_file.fileno())
        current = self._checked_stat(path)
        if _file_state(opened) != _file_state(after) or _file_state(after) != _file_state(current):
            raise OSError(f"Reference file changed during observation: {path}.")
        return f"sha256:{digest.hexdigest()}"

    def observe(self) -> tuple[ReferenceItemObservation, ...]:
        """Return a sorted complete snapshot, or propagate failure without partial success."""
        self._validate_root()
        directories = [self._root]
        observations: list[ReferenceItemObservation] = []
        seen_ids: set[str] = set()
        while directories:
            directory = directories.pop()
            if not stat.S_ISDIR(self._checked_stat(directory).st_mode):
                raise NotADirectoryError(f"Reference directory changed: {directory}.")
            with os.scandir(directory) as entries:
                for entry in entries:
                    path = directory / entry.name
                    metadata = self._checked_stat(path)
                    if stat.S_ISDIR(metadata.st_mode):
                        directories.append(path)
                    elif not stat.S_ISREG(metadata.st_mode):
                        raise ValueError(f"Reference path must be a regular file: {path}.")
                    elif path.suffix.lower() in _IMAGE_SUFFIXES:
                        item_id = path.relative_to(self._root).as_posix()
                        if item_id in seen_ids:
                            raise ValueError(
                                f"Duplicate observation for source item ID: {item_id}."
                            )
                        seen_ids.add(item_id)
                        observations.append(
                            ReferenceItemObservation(
                                self.source_id, item_id, self._content_hash(path, metadata)
                            )
                        )
        self._validate_root()
        return tuple(sorted(observations, key=lambda observation: observation.source_item_id))
