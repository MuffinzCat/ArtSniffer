"""Tests for provider-neutral image analysis benchmarking."""

from pathlib import Path

import pytest

import artsniffer.benchmark.runner as benchmark
from artsniffer.analysis.artwork import ArtworkAnalysis
from artsniffer.benchmark.models import BenchmarkAnalysis, BenchmarkImage
from artsniffer.benchmark.runner import (
    benchmark_analysers,
    benchmark_image,
    benchmark_images,
)


class FakeAnalyser:
    """Record calls and produce lightweight artwork analyses."""

    def __init__(
        self,
        model_id: str,
        calls: list[tuple[str, str, Path]],
        result: ArtworkAnalysis | None = None,
    ) -> None:
        self.model_id = model_id
        self.calls = calls
        self.result = result

    def analyse(self, artwork_id: str, image_path: Path) -> ArtworkAnalysis:
        self.calls.append((self.model_id, artwork_id, image_path))
        if self.result is not None:
            return self.result
        return ArtworkAnalysis(artwork_id=artwork_id, model_id=self.model_id, embedding=(0.5,))


def test_benchmark_containers_preserve_values() -> None:
    image = BenchmarkImage(artwork_id="art-1", image_path=Path("art-1.png"))
    analysis = ArtworkAnalysis(artwork_id="art-1", model_id="model-1", embedding=(0.5,))
    result = BenchmarkAnalysis(
        model_id="model-1", artwork_id="art-1", analysis=analysis, elapsed_seconds=1.25
    )

    assert image.artwork_id == "art-1"
    assert image.image_path == Path("art-1.png")
    assert result.model_id == "model-1"
    assert result.artwork_id == "art-1"
    assert result.analysis is analysis
    assert result.elapsed_seconds == 1.25


def test_benchmark_image_returns_analysis_and_elapsed_time(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str, Path]] = []
    analysis = ArtworkAnalysis(artwork_id="art-1", model_id="model-1", embedding=(0.5,))
    analyser = FakeAnalyser("model-1", calls, analysis)
    image = BenchmarkImage("art-1", Path("art-1.png"))
    clock_values = iter((10.0, 12.5))
    monkeypatch.setattr(benchmark, "perf_counter", lambda: next(clock_values))

    result = benchmark_image(analyser, image)

    assert calls == [("model-1", "art-1", image.image_path)]
    assert result.model_id == "model-1"
    assert result.artwork_id == "art-1"
    assert result.analysis is analysis
    assert result.elapsed_seconds == pytest.approx(2.5)


@pytest.mark.parametrize(
    ("analysis", "message"),
    [
        (
            ArtworkAnalysis(artwork_id="art-1", model_id="other-model", embedding=(0.5,)),
            "Analysis model ID must match analyser model ID.",
        ),
        (
            ArtworkAnalysis(artwork_id="other-art", model_id="model-1", embedding=(0.5,)),
            "Analysis artwork ID must match benchmark artwork ID.",
        ),
    ],
)
def test_benchmark_image_rejects_mismatched_identifiers(
    analysis: ArtworkAnalysis, message: str
) -> None:
    analyser = FakeAnalyser("model-1", [], analysis)

    with pytest.raises(ValueError) as error:
        benchmark_image(analyser, BenchmarkImage("art-1", Path("art-1.png")))

    assert str(error.value) == message


def test_benchmark_images_preserves_input_order() -> None:
    calls: list[tuple[str, str, Path]] = []
    analyser = FakeAnalyser("model-1", calls)
    images = (
        BenchmarkImage("art-2", Path("art-2.png")),
        BenchmarkImage("art-1", Path("art-1.png")),
    )

    results = benchmark_images(analyser, images)

    assert isinstance(results, tuple)
    assert [(result.model_id, result.artwork_id) for result in results] == [
        ("model-1", "art-2"),
        ("model-1", "art-1"),
    ]
    assert calls == [("model-1", image.artwork_id, image.image_path) for image in images]


def test_benchmark_images_with_no_images() -> None:
    calls: list[tuple[str, str, Path]] = []

    assert benchmark_images(FakeAnalyser("model-1", calls), ()) == ()
    assert calls == []


def test_benchmark_analysers_uses_analyser_major_order() -> None:
    calls: list[tuple[str, str, Path]] = []
    analysers = (FakeAnalyser("model-2", calls), FakeAnalyser("model-1", calls))
    images = (
        BenchmarkImage("art-2", Path("art-2.png")),
        BenchmarkImage("art-1", Path("art-1.png")),
    )

    results = benchmark_analysers(analysers, images)

    assert isinstance(results, tuple)
    assert [(result.model_id, result.artwork_id) for result in results] == [
        ("model-2", "art-2"),
        ("model-2", "art-1"),
        ("model-1", "art-2"),
        ("model-1", "art-1"),
    ]
    assert calls == [
        ("model-2", "art-2", Path("art-2.png")),
        ("model-2", "art-1", Path("art-1.png")),
        ("model-1", "art-2", Path("art-2.png")),
        ("model-1", "art-1", Path("art-1.png")),
    ]
    assert all(result.analysis.model_id == result.model_id for result in results)
    assert all(result.analysis.artwork_id == result.artwork_id for result in results)


@pytest.mark.parametrize(
    ("has_analysers", "has_images"), [(False, True), (True, False), (False, False)]
)
def test_benchmark_analysers_with_empty_inputs(has_analysers: bool, has_images: bool) -> None:
    calls: list[tuple[str, str, Path]] = []
    analysers = (FakeAnalyser("model-1", calls),) if has_analysers else ()
    images = (BenchmarkImage("art-1", Path("art-1.png")),) if has_images else ()

    assert benchmark_analysers(analysers, images) == ()
    assert calls == []
