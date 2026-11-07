"""DINOv2 image embeddings using the optional benchmark-dinov2 dependencies."""

from pathlib import Path

import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModel

from artsniffer.analysis.artwork import ArtworkAnalysis


class DinoV2ImageAnalyser:
    """Represent whole images with the facebook/dinov2-small CLS token."""

    model_id = "facebook/dinov2-small"

    def __init__(self) -> None:
        """Load and reuse the processor and evaluation-mode model.

        Hugging Face may download files that are not already cached locally.
        """
        self._processor = AutoImageProcessor.from_pretrained(self.model_id)
        self._model = AutoModel.from_pretrained(self.model_id)
        self._model.eval()

    def analyse(
        self,
        artwork_id: str,
        image_path: Path,
    ) -> ArtworkAnalysis:
        """Analyse a local image and return its CLS embedding as Python floats."""
        with Image.open(image_path) as source_image:
            image = source_image.convert("RGB")

        inputs = self._processor(images=image, return_tensors="pt")
        with torch.inference_mode():
            outputs = self._model(**inputs)
        # The first token summarises the whole image; the remaining tokens describe patches.
        embedding_tensor = outputs.last_hidden_state[0, 0]
        embedding = tuple(float(value) for value in embedding_tensor.tolist())
        return ArtworkAnalysis(artwork_id=artwork_id, model_id=self.model_id, embedding=embedding)
