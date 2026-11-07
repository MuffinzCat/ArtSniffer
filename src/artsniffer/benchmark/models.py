"""Records for benchmark images and analysis results."""

from dataclasses import dataclass
from pathlib import Path

from artsniffer.analysis.artwork import ArtworkAnalysis


@dataclass
class BenchmarkImage:
    """Identify an artwork and the image to analyse."""

    artwork_id: str
    image_path: Path


@dataclass
class BenchmarkAnalysis:
    """Store an analysis and the time taken to produce it."""

    model_id: str
    artwork_id: str
    analysis: ArtworkAnalysis
    elapsed_seconds: float
