"""Provider-neutral reuse of exact cached artwork image analysis."""

from pathlib import Path

from artsniffer.analysis.artwork import ArtworkAnalysis
from artsniffer.analysis.image_analyser import ImageAnalyser
from artsniffer.persistence.analysis_cache import AnalysisCache


def analyse_cached_image(
    artwork_id: str,
    content_hash: str,
    image_path: Path,
    *,
    analyser: ImageAnalyser,
    cache: AnalysisCache,
) -> ArtworkAnalysis:
    """Return exact cached analysis, or infer once, validate and store before returning.

    Callers own safety/rating authorisation, resource lifetimes and binding the supplied
    hash to the image bytes. Identities are not normalised; paths are not checked or read.
    The analyser's model ID must remain stable during the call. Cache and inference errors
    propagate without retries or fallback; neither mismatched nor failed analysis is stored.
    """
    if not isinstance(artwork_id, str) or not artwork_id.strip():
        raise ValueError("Artwork ID must not be empty or whitespace.")
    if not isinstance(content_hash, str) or not content_hash.strip():
        raise ValueError("Content hash must not be empty or whitespace.")
    model_id = analyser.model_id
    if not isinstance(model_id, str) or not model_id.strip():
        raise ValueError("Model ID must not be empty or whitespace.")
    if not isinstance(image_path, Path):
        raise ValueError("Image path must be a Path.")

    analysis = cache.get(artwork_id, content_hash, model_id)
    cache_miss = analysis is None
    if cache_miss:
        analysis = analyser.analyse(artwork_id, image_path)

    if not isinstance(analysis, ArtworkAnalysis):
        raise ValueError("Analysis result must be an ArtworkAnalysis.")
    if analysis.artwork_id != artwork_id:
        raise ValueError("Analysis artwork ID must match requested artwork ID.")
    if analysis.model_id != model_id:
        raise ValueError("Analysis model ID must match analyser model ID.")

    if cache_miss:
        cache.put(analysis, content_hash)
    return analysis
