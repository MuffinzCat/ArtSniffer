"""Tests for the provider-neutral image analysis protocol."""

from pathlib import Path

from artsniffer.analysis.artwork import ArtworkAnalysis
from artsniffer.analysis.image_analyser import ImageAnalyser


class StubImageAnalyser:
    """Provide a structurally compatible analyser for the protocol test."""

    model_id = "test-model-v1"

    def __init__(self) -> None:
        self.image_path: Path | None = None

    def analyse(self, artwork_id: str, image_path: Path) -> ArtworkAnalysis:
        """Record the image path and return an analysis for the artwork."""
        self.image_path = image_path
        return ArtworkAnalysis(artwork_id=artwork_id, model_id=self.model_id, embedding=(0.5,))


def test_image_analyser_accepts_structural_implementation() -> None:
    """An analyser can implement the protocol without inheriting from it."""
    stub = StubImageAnalyser()
    analyser: ImageAnalyser = stub
    image_path = Path("images") / "artwork.png"

    analysis = analyser.analyse("artwork-001", image_path)

    assert stub.image_path == image_path
    assert analysis.artwork_id == "artwork-001"
    assert analysis.model_id == analyser.model_id
    assert analysis.embedding == (0.5,)
