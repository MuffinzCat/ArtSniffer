"""Provider-neutral timing of image analysers over benchmark images."""

from time import perf_counter

from artsniffer.analysis.image_analyser import ImageAnalyser
from artsniffer.benchmark.analysis import BenchmarkAnalysis
from artsniffer.benchmark.dataset import BenchmarkImage


def benchmark_image(analyser: ImageAnalyser, benchmark_image: BenchmarkImage) -> BenchmarkAnalysis:
    """Time one analysis and verify its model and artwork identifiers."""
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
    """Benchmark one analyser on each image in input order."""
    return tuple(benchmark_image(analyser, image) for image in benchmark_images)


def benchmark_analysers(
    analysers: tuple[ImageAnalyser, ...], benchmark_images: tuple[BenchmarkImage, ...]
) -> tuple[BenchmarkAnalysis, ...]:
    """Benchmark every analyser on every image, ordered by analyser then image."""
    return tuple(
        benchmark_image(analyser, image) for analyser in analysers for image in benchmark_images
    )
