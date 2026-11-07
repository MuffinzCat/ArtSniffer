"""Tests for loading benchmark image datasets."""

from pathlib import Path

import pytest

from artsniffer.benchmark.dataset import load_benchmark_images
from artsniffer.benchmark.models import BenchmarkImage


def test_load_benchmark_images_with_one_image(tmp_path: Path) -> None:
    dataset_path = tmp_path / "dataset.toml"
    image_path = tmp_path / "images" / "art-1.png"
    image_path.parent.mkdir()
    image_path.write_bytes(b"")
    dataset_path.write_text(
        '[[images]]\nartwork_id = "art-1"\npath = "images/art-1.png"\n',
        encoding="utf-8",
    )

    images = load_benchmark_images(dataset_path)

    assert isinstance(images, tuple)
    assert len(images) == 1
    assert isinstance(images[0], BenchmarkImage)
    assert images[0].artwork_id == "art-1"
    assert images[0].image_path == image_path


def test_load_benchmark_images_preserves_manifest_order(tmp_path: Path) -> None:
    dataset_path = tmp_path / "dataset.toml"
    image_paths = (tmp_path / "first.png", tmp_path / "second.png")
    for image_path in image_paths:
        image_path.write_bytes(b"")
    dataset_path.write_text(
        '[[images]]\nartwork_id = "art-2"\npath = "first.png"\n\n'
        '[[images]]\nartwork_id = "art-1"\npath = "second.png"\n',
        encoding="utf-8",
    )

    images = load_benchmark_images(dataset_path)

    assert tuple((image.artwork_id, image.image_path) for image in images) == (
        ("art-2", image_paths[0]),
        ("art-1", image_paths[1]),
    )
    assert all(isinstance(image, BenchmarkImage) for image in images)


def test_load_benchmark_images_resolves_paths_from_manifest_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dataset_path = tmp_path / "manifests" / "dataset.toml"
    image_path = dataset_path.parent / "art-1.png"
    dataset_path.parent.mkdir()
    image_path.write_bytes(b"")
    dataset_path.write_text(
        '[[images]]\nartwork_id = "art-1"\npath = "art-1.png"\n',
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    images = load_benchmark_images(dataset_path)

    assert images[0].image_path == image_path
    assert images[0].image_path.is_file()


def test_load_benchmark_images_with_empty_images_array(tmp_path: Path) -> None:
    dataset_path = tmp_path / "dataset.toml"
    dataset_path.write_text("images = []\n", encoding="utf-8")

    assert load_benchmark_images(dataset_path) == ()
