from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

from artsniffer.analysis.artwork import ArtworkAnalysis
from artsniffer.analysis.image_analyser import ImageAnalyser


@dataclass
class BenchmarkImage:
    artwork_id: str
    image_path: Path


@dataclass
class BenchmarkAnalysis:
    model_id: str
    artwork_id: str
    analysis: ArtworkAnalysis
    elapsed_seconds: float


def benchmark_image(analyser: ImageAnalyser, benchmark_image: BenchmarkImage) -> BenchmarkAnalysis:
    start = perf_counter()
    analysis = analyser.analyse(benchmark_image.artwork_id, benchmark_image.image_path)
    elapsed_seconds = perf_counter() - start
    if analysis.model_id != analyser.model_id:
        raise ValueError("Analysis model ID must match analyser model ID.")
    if analysis.artwork_id != benchmark_image.artwork_id:
        raise ValueError("Analysis artwork ID must match benchmark artwork ID.")
    return BenchmarkAnalysis(
        model_id=analyser.model_id,
        artwork_id=benchmark_image.artwork_id,
        analysis=analysis,
        elapsed_seconds=elapsed_seconds,
    )


def benchmark_images(
    analyser: ImageAnalyser, benchmark_images: tuple[BenchmarkImage, ...]
) -> tuple[BenchmarkAnalysis, ...]:
    return tuple(benchmark_image(analyser, img) for img in benchmark_images)
