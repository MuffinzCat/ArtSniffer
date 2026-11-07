"""Offline tests for DINOv2 loading and whole-image embedding extraction."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest
import torch

import artsniffer.analysis.dinov2_analyser as dinov2
from artsniffer.analysis.artwork import ArtworkAnalysis


@pytest.fixture
def model_loaders(monkeypatch: pytest.MonkeyPatch) -> tuple[Mock, Mock]:
    """Replace both Hugging Face loaders before any analyser is constructed."""
    processor_loader = Mock(return_value=Mock())
    model_loader = Mock(return_value=Mock())
    monkeypatch.setattr(dinov2.AutoImageProcessor, "from_pretrained", processor_loader)
    monkeypatch.setattr(dinov2.AutoModel, "from_pretrained", model_loader)
    return processor_loader, model_loader


def test_initialisation_loads_identified_processor_and_evaluation_model(
    model_loaders: tuple[Mock, Mock],
) -> None:
    processor_loader, model_loader = model_loaders

    analyser = dinov2.DinoV2ImageAnalyser()

    assert analyser.model_id == "facebook/dinov2-small"
    processor_loader.assert_called_once_with(analyser.model_id)
    model_loader.assert_called_once_with(analyser.model_id)
    model_loader.return_value.eval.assert_called_once_with()


def test_analyse_preprocesses_rgb_image_and_returns_cls_embedding(
    monkeypatch: pytest.MonkeyPatch, model_loaders: tuple[Mock, Mock]
) -> None:
    processor_loader, model_loader = model_loaders
    processor = processor_loader.return_value
    model = model_loader.return_value
    image_path = Path("images") / "synthetic.png"
    source_image = MagicMock()
    rgb_image = source_image.convert.return_value
    source_image.__enter__.return_value = source_image
    open_image = Mock(return_value=source_image)
    monkeypatch.setattr(dinov2.Image, "open", open_image)
    pixels = torch.zeros((1, 3, 2, 2))
    processor.return_value = {"pixel_values": pixels}
    hidden_state = torch.tensor(
        [
            [[1, -2, 3], [10, 20, 30]],
            [[100, 200, 300], [1000, 2000, 3000]],
        ]
    )

    def infer(*, pixel_values: torch.Tensor) -> SimpleNamespace:
        assert pixel_values is pixels
        assert torch.is_inference_mode_enabled()
        assert not torch.is_grad_enabled()
        return SimpleNamespace(last_hidden_state=hidden_state)

    model.side_effect = infer
    analyser = dinov2.DinoV2ImageAnalyser()

    analysis = analyser.analyse("artwork-001", image_path)

    open_image.assert_called_once_with(image_path)
    source_image.__enter__.assert_called_once_with()
    source_image.convert.assert_called_once_with("RGB")
    source_image.__exit__.assert_called_once_with(None, None, None)
    processor.assert_called_once_with(images=rgb_image, return_tensors="pt")
    model.assert_called_once()
    assert isinstance(analysis, ArtworkAnalysis)
    assert analysis.artwork_id == "artwork-001"
    assert analysis.model_id == analyser.model_id
    assert analysis.embedding == (1.0, -2.0, 3.0)
    assert isinstance(analysis.embedding, tuple)
    assert all(isinstance(value, float) for value in analysis.embedding)


def test_repeated_analysis_reuses_loaded_processor_and_model(
    monkeypatch: pytest.MonkeyPatch, model_loaders: tuple[Mock, Mock]
) -> None:
    processor_loader, model_loader = model_loaders
    monkeypatch.setattr(dinov2.Image, "open", MagicMock())
    processor_loader.return_value.return_value = {"pixel_values": torch.zeros((1, 3, 2, 2))}
    model_loader.return_value.return_value = SimpleNamespace(
        last_hidden_state=torch.tensor([[[0.5]]])
    )
    analyser = dinov2.DinoV2ImageAnalyser()

    first = analyser.analyse("artwork-001", Path("first.png"))
    second = analyser.analyse("artwork-002", Path("second.png"))

    assert first.artwork_id == "artwork-001"
    assert second.artwork_id == "artwork-002"
    processor_loader.assert_called_once_with(analyser.model_id)
    model_loader.assert_called_once_with(analyser.model_id)
    model_loader.return_value.eval.assert_called_once_with()
    assert processor_loader.return_value.call_count == 2
    assert model_loader.return_value.call_count == 2
