"""Load benchmark image records from a TOML dataset manifest."""

import tomllib
from pathlib import Path

from artsniffer.benchmark.models import BenchmarkImage


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
