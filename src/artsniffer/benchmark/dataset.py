"""Load benchmark images and expected comparisons from a TOML dataset manifest."""

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class BenchmarkImage:
    """Identify an artwork and the image to analyse."""

    artwork_id: str
    image_path: Path


@dataclass
class BenchmarkComparison:
    """Identify a manifest-selected query and its expected strong and weak matches."""

    query_artwork_id: str
    strong_expected_match_id: str
    weak_expected_match_id: str


def load_benchmark_images(dataset_path: Path) -> tuple[BenchmarkImage, ...]:
    """Read ``[[images]]`` and return records with paths relative to the manifest."""
    with dataset_path.open("rb") as dataset_file:
        manifest_data = tomllib.load(dataset_file)
    dataset_directory = dataset_path.parent
    benchmark_images: list[BenchmarkImage] = []
    for image_entry in manifest_data["images"]:
        artwork_id = image_entry["artwork_id"]
        relative_path = image_entry["path"]
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
        manifest_data = tomllib.load(dataset_file)
    comparisons: list[BenchmarkComparison] = []
    for comparison_entry in manifest_data.get("comparisons", ()):
        query_artwork_id = comparison_entry["query_artwork_id"]
        strong_expected_match_id = comparison_entry["strong_expected_match_id"]
        weak_expected_match_id = comparison_entry["weak_expected_match_id"]
        comparisons.append(
            BenchmarkComparison(
                query_artwork_id=query_artwork_id,
                strong_expected_match_id=strong_expected_match_id,
                weak_expected_match_id=weak_expected_match_id,
            )
        )
    return tuple(comparisons)
