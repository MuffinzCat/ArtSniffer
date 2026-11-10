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
class ArtSnifferSettings:
    """Validated settings loaded for the ArtSniffer application."""

    reference_libraries: tuple[LocalReferenceLibrarySettings, ...]

    def __post_init__(self) -> None:
        seen_source_ids = set()
        for reference_library in self.reference_libraries:
            if reference_library.source_id in seen_source_ids:
                raise ValueError(f"duplicate source ID: {reference_library.source_id}")
            seen_source_ids.add(reference_library.source_id)


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
    return ArtSnifferSettings(reference_libraries=tuple(parsed_reference_libraries))
