"""Provider-neutral interface for artwork image analysis."""

from pathlib import Path
from typing import Protocol

from artsniffer.analysis.artwork import ArtworkAnalysis


class ImageAnalyser(Protocol):
    """Analyse artwork images using an identified model."""

    model_id: str

    def analyse(self, artwork_id: str, image_path: Path) -> ArtworkAnalysis:
        """Analyse an image for an artwork.

        Implementations must return an analysis whose model ID matches their own.
        """
        ...
