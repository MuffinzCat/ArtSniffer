"""Safe same-directory replacement for complete snapshot and state files."""

import os
import tempfile
from pathlib import Path


def safe_write(path: Path, content: bytes, *, overwrite: bool) -> None:
    """Publish complete bytes and clean only the temporary file created by this call.

    Replacement uses ``os.replace``; create-only publication uses a hard link so an existing
    destination cannot be overwritten, including if it appears after the initial existence check.
    Atomicity depends on the host filesystem's support for these same-directory operations.
    """
    if not overwrite and path.exists():
        raise FileExistsError(f"File already exists: {path}.")

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary_path = Path(temporary_name)
    try:
        stream = os.fdopen(descriptor, "wb")
        descriptor = -1
        with stream:
            stream.write(content)
            stream.flush()

        if overwrite:
            os.replace(temporary_path, path)
        else:
            os.link(temporary_path, path)
    finally:
        try:
            if descriptor >= 0:
                os.close(descriptor)
        finally:
            temporary_path.unlink(missing_ok=True)
