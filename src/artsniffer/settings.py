"""Load, validate, and locate ArtSniffer configuration."""

import os
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LocalReferenceLibrarySettings:
    """Settings for one local reference library and its managed state file."""

    source_id: str
    folder: Path
    state_file: Path

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError("source ID cannot be empty or whitespace")


@dataclass(frozen=True)
class BlueskyDiscoverySettings:
    """Configure one bounded, anonymous Bluesky getFeed source."""

    source_id: str
    feed_uri: str
    kind: str = "bluesky"
    enabled: bool = True
    limit: int = 50
    timeout_seconds: float = 10.0

    def __post_init__(self) -> None:
        """Validate stable source identity and bounded public request parameters."""
        if not self.source_id.strip():
            raise ValueError("Bluesky source ID must not be empty or whitespace.")
        if not self.feed_uri.strip():
            raise ValueError("Bluesky feed URI must not be empty or whitespace.")
        if not self.feed_uri.startswith("at://"):
            raise ValueError("Bluesky feed URI must be an AT URI.")
        if not self.kind.strip():
            raise ValueError("Bluesky provider kind must not be empty or whitespace.")
        if self.kind != "bluesky":
            raise ValueError("Bluesky provider kind must be 'bluesky'.")
        if isinstance(self.limit, bool) or not isinstance(self.limit, int):
            raise ValueError("Bluesky result limit must be an integer.")
        if not 1 <= self.limit <= 100:
            raise ValueError("Bluesky result limit must be between 1 and 100.")
        if isinstance(self.timeout_seconds, bool) or not isinstance(
            self.timeout_seconds, (int, float)
        ):
            raise ValueError("Bluesky timeout must be a number.")
        if not 0 < self.timeout_seconds <= 60:
            raise ValueError("Bluesky timeout must be greater than 0 and at most 60 seconds.")


@dataclass(frozen=True)
class E621DiscoverySettings:
    """Configure one bounded, anonymous e621/e926 discovery source."""

    source_id: str
    host: str
    tag_search_expressions: tuple[str, ...]
    client_contact: str
    enabled: bool = True
    limit: int = 50
    timeout_seconds: float = 10.0

    def __post_init__(self) -> None:
        """Validate provider identity, tag expressions, and bounded request parameters."""
        if not self.source_id.strip():
            raise ValueError("e621 source ID must not be empty or whitespace.")
        if not self.host.strip():
            raise ValueError("e621 host must not be empty or whitespace.")
        if self.host != "e621.net" and self.host != "e926.net":
            raise ValueError("e621 host must be either 'e621.net' or 'e926.net'.")
        if not self.tag_search_expressions:
            raise ValueError("e621 tag search expressions must not be empty.")
        if not all(isinstance(tag, str) and tag.strip() for tag in self.tag_search_expressions):
            raise ValueError("e621 tag search expressions must be non-empty strings.")
        if not self.client_contact.strip():
            raise ValueError("e621 client contact must not be empty or whitespace.")
        if isinstance(self.limit, bool) or not isinstance(self.limit, int):
            raise ValueError("e621 result limit must be an integer.")
        if not 1 <= self.limit <= 100:
            raise ValueError("e621 result limit must be between 1 and 100.")
        if isinstance(self.timeout_seconds, bool) or not isinstance(
            self.timeout_seconds, (int, float)
        ):
            raise ValueError("e621 timeout must be a number.")
        if not 0 < self.timeout_seconds <= 60:
            raise ValueError("e621 timeout must be greater than 0 and at most 60 seconds.")


@dataclass(frozen=True)
class ArtSnifferSettings:
    """Validated settings loaded for the ArtSniffer application."""

    reference_libraries: tuple[LocalReferenceLibrarySettings, ...]
    bluesky_discovery_sources: tuple[BlueskyDiscoverySettings, ...] = ()
    e621_discovery_sources: tuple[E621DiscoverySettings, ...] = ()

    def __post_init__(self) -> None:
        seen_source_ids = set()
        for reference_library in self.reference_libraries:
            if reference_library.source_id in seen_source_ids:
                raise ValueError(f"duplicate source ID: {reference_library.source_id}")
            seen_source_ids.add(reference_library.source_id)
        for discovery_source in self.bluesky_discovery_sources:
            if discovery_source.source_id in seen_source_ids:
                raise ValueError(f"duplicate source ID: {discovery_source.source_id}")
            seen_source_ids.add(discovery_source.source_id)
        for discovery_source in self.e621_discovery_sources:
            if discovery_source.source_id in seen_source_ids:
                raise ValueError(f"duplicate source ID: {discovery_source.source_id}")
            seen_source_ids.add(discovery_source.source_id)


def parse_local_reference_library(
    library_data: dict[str, object], config_directory: Path
) -> LocalReferenceLibrarySettings:
    """Validate and parse one local reference-library configuration."""
    source_id = library_data.get("source_id")
    if not isinstance(source_id, str):
        raise ValueError("source ID must be a string")

    folder = library_data.get("folder")
    if not isinstance(folder, str):
        raise ValueError("folder must be a string")
    if not folder.strip():
        raise ValueError("folder cannot be empty or whitespace")
    state_file = library_data.get("state_file")
    if not isinstance(state_file, str):
        raise ValueError("state file must be a string")
    if not state_file.strip():
        raise ValueError("state file cannot be empty or whitespace")

    folder_path = Path(folder)
    if not folder_path.is_absolute():
        folder_path = config_directory / folder_path
    state_file_path = Path(state_file)
    if not state_file_path.is_absolute():
        state_file_path = config_directory / state_file_path

    return LocalReferenceLibrarySettings(
        source_id=source_id, folder=folder_path, state_file=state_file_path
    )


def parse_bluesky_discovery_source(
    source_data: dict[str, object],
) -> BlueskyDiscoverySettings:
    """Validate and parse one anonymous Bluesky getFeed source."""
    source_id = source_data.get("source_id")
    if not isinstance(source_id, str):
        raise ValueError("Bluesky source ID must be a string.")
    feed_uri = source_data.get("feed_uri")
    if not isinstance(feed_uri, str):
        raise ValueError("Bluesky feed URI must be a string.")
    kind = source_data.get("kind", "bluesky")
    if not isinstance(kind, str):
        raise ValueError("Bluesky provider kind must be a string.")
    enabled = source_data.get("enabled", True)
    if not isinstance(enabled, bool):
        raise ValueError("Bluesky enabled state must be a boolean.")
    limit = source_data.get("limit", 50)
    if not isinstance(limit, int) or isinstance(limit, bool):
        raise ValueError("Bluesky result limit must be an integer.")
    timeout_seconds = source_data.get("timeout_seconds", 10.0)
    if not isinstance(timeout_seconds, (int, float)) or isinstance(timeout_seconds, bool):
        raise ValueError("Bluesky timeout must be a number.")
    return BlueskyDiscoverySettings(
        source_id=source_id,
        feed_uri=feed_uri,
        kind=kind,
        enabled=enabled,
        limit=limit,
        timeout_seconds=float(timeout_seconds),
    )


def parse_e621_discovery_source(
    source_data: dict[str, object],
) -> E621DiscoverySettings:
    """Validate raw TOML values and convert one e621/e926 source to settings."""
    source_id = source_data.get("source_id")
    if not isinstance(source_id, str):
        raise ValueError("e621 source ID must be a string.")
    host = source_data.get("host")
    if not isinstance(host, str):
        raise ValueError("e621 host must be a string.")
    tag_search_expressions = source_data.get("tag_search_expressions")
    if not isinstance(tag_search_expressions, list):
        raise ValueError("e621 tag search expressions must be a list.")
    for expression in tag_search_expressions:
        if not isinstance(expression, str):
            raise ValueError("each e621 tag search expression must be a string.")
    client_contact = source_data.get("client_contact")
    if not isinstance(client_contact, str):
        raise ValueError("e621 client contact must be a string.")
    enabled = source_data.get("enabled", True)
    if not isinstance(enabled, bool):
        raise ValueError("e621 enabled state must be a boolean.")
    limit = source_data.get("limit", 50)
    if not isinstance(limit, int) or isinstance(limit, bool):
        raise ValueError("e621 result limit must be an integer.")
    timeout_seconds = source_data.get("timeout_seconds", 10.0)
    if not isinstance(timeout_seconds, (int, float)) or isinstance(timeout_seconds, bool):
        raise ValueError("e621 timeout must be a number.")
    return E621DiscoverySettings(
        source_id=source_id,
        host=host,
        tag_search_expressions=tuple(tag_search_expressions),
        client_contact=client_contact,
        enabled=enabled,
        limit=limit,
        timeout_seconds=float(timeout_seconds),
    )


def load_settings(config_path: Path) -> ArtSnifferSettings:
    """Load and validate ArtSniffer settings from a TOML file."""
    with config_path.open("rb") as config_file:
        config_data = tomllib.load(config_file)
    reference_libraries = config_data.get("reference_libraries", [])
    if not isinstance(reference_libraries, list):
        raise ValueError("reference_libraries must be a list")
    parsed_reference_libraries = []
    for reference_library in reference_libraries:
        if not isinstance(reference_library, dict):
            raise ValueError("each reference library must be a dictionary")
        parsed_reference_libraries.append(
            parse_local_reference_library(reference_library, config_path.parent)
        )
    bluesky_sources = config_data.get("bluesky_discovery_sources", [])
    if not isinstance(bluesky_sources, list):
        raise ValueError("bluesky_discovery_sources must be a list")
    parsed_bluesky_sources = []
    for bluesky_source in bluesky_sources:
        if not isinstance(bluesky_source, dict):
            raise ValueError("each Bluesky discovery source must be a dictionary")
        parsed_bluesky_sources.append(parse_bluesky_discovery_source(bluesky_source))
    e621_sources = config_data.get("e621_discovery_sources", [])
    if not isinstance(e621_sources, list):
        raise ValueError("e621_discovery_sources must be a list")
    parsed_e621_sources = []
    for e621_source in e621_sources:
        if not isinstance(e621_source, dict):
            raise ValueError("each e621 discovery source must be a dictionary")
        parsed_e621_sources.append(parse_e621_discovery_source(e621_source))
    return ArtSnifferSettings(
        reference_libraries=tuple(parsed_reference_libraries),
        bluesky_discovery_sources=tuple(parsed_bluesky_sources),
        e621_discovery_sources=tuple(parsed_e621_sources),
    )


def find_config_path(explicit_config_path: Path | None) -> Path:
    """Find an explicit or overridden config file, or the supported OS default location."""
    if explicit_config_path is not None:
        if explicit_config_path.is_file():
            return explicit_config_path
        raise FileNotFoundError(
            f"Configuration file does not exist or is not a file: {explicit_config_path}"
        )
    config_location = os.environ.get("ARTSNIFFER_CONFIG")
    if config_location is not None and config_location.strip():
        config_path = Path(config_location)
        if config_path.is_absolute():
            if config_path.is_file():
                return config_path
            raise FileNotFoundError(
                f"Configuration file does not exist or is not a file: {config_path}"
            )
        raise RuntimeError("ARTSNIFFER_CONFIG environment variable must be an absolute path")
    if sys.platform == "win32":
        local_windows_appdata = os.environ.get("LOCALAPPDATA", "").strip()
        if local_windows_appdata:
            local_windows_appdata_path = Path(local_windows_appdata)
            if local_windows_appdata_path.is_absolute():
                return local_windows_appdata_path / "ArtSniffer" / "config.toml"
    if sys.platform == "linux":
        xdg_config_home = os.environ.get("XDG_CONFIG_HOME", "").strip()
        if xdg_config_home:
            xdg_config_home_path = Path(xdg_config_home)
            if xdg_config_home_path.is_absolute():
                linux_config_path = xdg_config_home_path / "artsniffer" / "config.toml"
                return linux_config_path
        linux_home = os.environ.get("HOME", "").strip()
        if linux_home:
            linux_home_path = Path(linux_home)
            if linux_home_path.is_absolute():
                return linux_home_path / ".config" / "artsniffer" / "config.toml"
    raise RuntimeError(
        "ArtSniffer could not determine a default configuration location "
        "for this operating system/environment."
    )


def create_initial_config(config_path: Path) -> bool:
    """Create the initial configuration if it does not already exist.

    Returns:
        bool: True if the configuration file was created, False if it already existed.
    """
    if config_path.exists():
        if config_path.is_file():
            return False
        raise FileExistsError(f"Configuration path exists but is not a file: {config_path}")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with config_path.open("x", encoding="utf-8", newline="\n") as file:
            file.write("reference_libraries = []\n")
            return True
    except FileExistsError:
        if config_path.is_file():
            return False
        raise
