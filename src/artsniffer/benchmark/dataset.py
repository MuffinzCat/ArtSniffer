"""Load benchmark images and expected comparisons from a TOML dataset manifest."""

import tomllib
from pathlib import Path

from artsniffer.benchmark.models import BenchmarkComparison, BenchmarkImage


def load_benchmark_images(dataset_path: Path) -> tuple[BenchmarkImage, ...]:
    """Read ``[[images]]`` and return records with paths relative to the manifest."""
    with dataset_path.open("rb") as dataset_file:
        dataset = tomllib.load(dataset_file)
    dataset_directory = dataset_path.parent
    benchmark_images: list[BenchmarkImage] = []
    for image_data in dataset["images"]:
        artwork_id = image_data["artwork_id"]
        relative_path = image_data["path"]
        artwork_path = dataset_directory / relative_path
        benchmark_images.append(
            BenchmarkImage(
                artwork_id=artwork_id,
                image_path=artwork_path,
            )
        )
    return tuple(benchmark_images)


def load_benchmark_comparisons(
    dataset_path: Path,
) -> tuple[BenchmarkComparison, ...]:
    """Read optional ``[[comparisons]]`` in manifest order, preserving artwork IDs."""
    with dataset_path.open("rb") as dataset_file:
        dataset = tomllib.load(dataset_file)
    comparisons: list[BenchmarkComparison] = []
    for comparison_data in dataset.get("comparisons", ()):
        query_artwork_id = comparison_data["query_artwork_id"]
        strong_expected_match_id = comparison_data["strong_expected_match_id"]
        weak_expected_match_id = comparison_data["weak_expected_match_id"]
        comparisons.append(
            BenchmarkComparison(
                query_artwork_id=query_artwork_id,
                strong_expected_match_id=strong_expected_match_id,
                weak_expected_match_id=weak_expected_match_id,
            )
        )
    return tuple(comparisons)
