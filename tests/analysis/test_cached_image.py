"""Tests for provider-neutral exact cached image analysis orchestration."""

import ast
from pathlib import Path
from unittest.mock import Mock

import pytest

from artsniffer.analysis.artwork import ArtworkAnalysis
from artsniffer.analysis.cached_image import analyse_cached_image


class RecordingCache:
    """Retain exact-key results and record cache operations."""

    def __init__(self, events: list[tuple]) -> None:
        self.events = events
        self.entries: dict[tuple[str, str, str], ArtworkAnalysis] = {}

    def get(self, artwork_id: str, content_hash: str, model_id: str) -> ArtworkAnalysis | None:
        self.events.append(("get", artwork_id, content_hash, model_id))
        return self.entries.get((artwork_id, content_hash, model_id))

    def put(self, analysis: ArtworkAnalysis, content_hash: str) -> None:
        self.events.append(("put", analysis, content_hash))
        self.entries[(analysis.artwork_id, content_hash, analysis.model_id)] = analysis


class RecordingAnalyser:
    """Record inference without opening an image or loading a model."""

    def __init__(self, events: list[tuple], model_id: str = "model-v1") -> None:
        self.events = events
        self.model_id = model_id
        self.results: list[ArtworkAnalysis] = []

    def analyse(self, artwork_id: str, image_path: Path) -> ArtworkAnalysis:
        self.events.append(("analyse", artwork_id, image_path))
        result = ArtworkAnalysis(artwork_id, self.model_id, (0.5,), ("watercolour",))
        self.results.append(result)
        return result


def test_hit_returns_identical_cached_analysis_without_inference_or_write() -> None:
    events: list[tuple] = []
    cache = RecordingCache(events)
    analyser = RecordingAnalyser(events, " Model-V1 ")
    cached = ArtworkAnalysis(" Artwork-1 ", analyser.model_id, (0.5,), ("watercolour",))
    cache.entries[(cached.artwork_id, " Opaque-Hash ", analyser.model_id)] = cached

    result = analyse_cached_image(
        cached.artwork_id,
        " Opaque-Hash ",
        Path("nonexistent.png"),
        analyser=analyser,
        cache=cache,
    )

    assert result is cached
    assert events == [("get", " Artwork-1 ", " Opaque-Hash ", " Model-V1 ")]


def test_miss_gets_analyses_and_stores_in_order_without_normalising_identity() -> None:
    events: list[tuple] = []
    cache = RecordingCache(events)
    analyser = RecordingAnalyser(events, " Model-V1 ")
    image_path = Path("images") / "artwork.png"

    result = analyse_cached_image(
        " Artwork-1 ", " Opaque-Hash ", image_path, analyser=analyser, cache=cache
    )

    assert events == [
        ("get", " Artwork-1 ", " Opaque-Hash ", " Model-V1 "),
        ("analyse", " Artwork-1 ", image_path),
        ("put", result, " Opaque-Hash "),
    ]
    assert events[2][1] is result
    assert result is analyser.results[0]
    assert result is cache.entries[(" Artwork-1 ", " Opaque-Hash ", " Model-V1 ")]
    assert result.embedding == (0.5,)
    assert result.tags == ("watercolour",)


@pytest.mark.parametrize("second_path", [Path("first.png"), Path("different.png")])
def test_repeated_exact_key_reuses_analysis_regardless_of_image_path(second_path: Path) -> None:
    events: list[tuple] = []
    cache = RecordingCache(events)
    analyser = RecordingAnalyser(events)
    first_path = Path("first.png")

    first = analyse_cached_image("art-1", "hash-1", first_path, analyser=analyser, cache=cache)
    second = analyse_cached_image("art-1", "hash-1", second_path, analyser=analyser, cache=cache)

    assert second is first
    assert events == [
        ("get", "art-1", "hash-1", "model-v1"),
        ("analyse", "art-1", first_path),
        ("put", first, "hash-1"),
        ("get", "art-1", "hash-1", "model-v1"),
    ]


@pytest.mark.parametrize(
    ("content_hash", "model_id"),
    [
        ("hash-2", "model-v1"),
        ("hash-1", "model-v2"),
        (" hash-1 ", "model-v1"),
        ("HASH-1", "model-v1"),
        ("hash-1", " model-v1 "),
        ("hash-1", "MODEL-V1"),
    ],
)
def test_changed_content_or_model_identity_causes_miss(content_hash: str, model_id: str) -> None:
    events: list[tuple] = []
    cache = RecordingCache(events)
    analyser = RecordingAnalyser(events)
    path = Path("image.png")
    first = analyse_cached_image("art-1", "hash-1", path, analyser=analyser, cache=cache)
    events.clear()
    analyser.model_id = model_id

    changed = analyse_cached_image("art-1", content_hash, path, analyser=analyser, cache=cache)

    assert changed is not first
    assert events == [
        ("get", "art-1", content_hash, model_id),
        ("analyse", "art-1", path),
        ("put", changed, content_hash),
    ]
    assert cache.entries[("art-1", "hash-1", "model-v1")] is first


@pytest.mark.parametrize("field", ["artwork_id", "content_hash", "model_id"])
@pytest.mark.parametrize("invalid", ["", " \t\n", None, 123])
def test_invalid_identity_fails_before_cache_access(field: str, invalid: object) -> None:
    cache = Mock()
    analyser = Mock(model_id="model-v1")
    artwork_id = invalid if field == "artwork_id" else "art-1"
    content_hash = invalid if field == "content_hash" else "hash-1"
    if field == "model_id":
        analyser.model_id = invalid
    label = {"artwork_id": "Artwork ID", "content_hash": "Content hash", "model_id": "Model ID"}

    with pytest.raises(ValueError) as error:
        analyse_cached_image(
            artwork_id,  # type: ignore[arg-type]
            content_hash,  # type: ignore[arg-type]
            Path("image.png"),
            analyser=analyser,
            cache=cache,
        )

    assert str(error.value) == f"{label[field]} must not be empty or whitespace."
    assert cache.mock_calls == []
    analyser.analyse.assert_not_called()


@pytest.mark.parametrize("image_path", ["image.png", None, 123])
def test_invalid_image_path_fails_before_cache_access_even_for_hit(image_path: object) -> None:
    cache = Mock()
    cache.get.return_value = ArtworkAnalysis("art-1", "model-v1", (0.5,))
    analyser = Mock(model_id="model-v1")

    with pytest.raises(ValueError) as error:
        analyse_cached_image(
            "art-1",
            "hash-1",
            image_path,  # type: ignore[arg-type]
            analyser=analyser,
            cache=cache,
        )

    assert str(error.value) == "Image path must be a Path."
    assert cache.mock_calls == []
    analyser.analyse.assert_not_called()


@pytest.mark.parametrize("cache_hit", [True, False], ids=["cached", "inferred"])
@pytest.mark.parametrize(
    ("result", "message"),
    [
        (object(), "Analysis result must be an ArtworkAnalysis."),
        (
            ArtworkAnalysis("other-art", "model-v1", (0.5,)),
            "Analysis artwork ID must match requested artwork ID.",
        ),
        (
            ArtworkAnalysis("art-1", "other-model", (0.5,)),
            "Analysis model ID must match analyser model ID.",
        ),
        (
            ArtworkAnalysis("other-art", "other-model", (0.5,)),
            "Analysis artwork ID must match requested artwork ID.",
        ),
        (
            ArtworkAnalysis(" art-1 ", "model-v1", (0.5,)),
            "Analysis artwork ID must match requested artwork ID.",
        ),
        (
            ArtworkAnalysis("art-1", "MODEL-V1", (0.5,)),
            "Analysis model ID must match analyser model ID.",
        ),
    ],
)
def test_cached_and_inferred_results_require_exact_analysis_identity(
    cache_hit: bool, result: object, message: str
) -> None:
    cache = Mock()
    cache.get.return_value = result if cache_hit else None
    analyser = Mock(model_id="model-v1")
    analyser.analyse.return_value = result
    path = Path("image.png")

    with pytest.raises(ValueError) as error:
        analyse_cached_image("art-1", "hash-1", path, analyser=analyser, cache=cache)

    assert str(error.value) == message
    cache.get.assert_called_once_with("art-1", "hash-1", "model-v1")
    cache.put.assert_not_called()
    if cache_hit:
        analyser.analyse.assert_not_called()
    else:
        analyser.analyse.assert_called_once_with("art-1", path)


def test_none_inference_result_is_rejected_without_write() -> None:
    cache = Mock()
    cache.get.return_value = None
    analyser = Mock(model_id="model-v1")
    analyser.analyse.return_value = None
    path = Path("image.png")

    with pytest.raises(ValueError) as error:
        analyse_cached_image("art-1", "hash-1", path, analyser=analyser, cache=cache)

    assert str(error.value) == "Analysis result must be an ArtworkAnalysis."
    cache.get.assert_called_once_with("art-1", "hash-1", "model-v1")
    analyser.analyse.assert_called_once_with("art-1", path)
    cache.put.assert_not_called()


@pytest.mark.parametrize("failure_stage", ["get", "analyse", "put"])
def test_operation_errors_propagate_without_retry_or_fallback(failure_stage: str) -> None:
    cache = Mock()
    cache.get.return_value = None
    analysis = ArtworkAnalysis("art-1", "model-v1", (0.5,))
    analyser = Mock(model_id="model-v1")
    analyser.analyse.return_value = analysis
    failure = RuntimeError(f"{failure_stage} failed")
    operation = analyser.analyse if failure_stage == "analyse" else getattr(cache, failure_stage)
    operation.side_effect = failure
    path = Path("image.png")

    with pytest.raises(RuntimeError) as error:
        analyse_cached_image("art-1", "hash-1", path, analyser=analyser, cache=cache)

    assert error.value is failure
    cache.get.assert_called_once_with("art-1", "hash-1", "model-v1")
    if failure_stage == "get":
        analyser.analyse.assert_not_called()
    else:
        analyser.analyse.assert_called_once_with("art-1", path)
    if failure_stage == "put":
        cache.put.assert_called_once_with(analysis, "hash-1")
    else:
        cache.put.assert_not_called()


def test_cached_image_module_has_only_agreed_neutral_dependencies() -> None:
    module_path = (
        Path(__file__).resolve().parents[2] / "src" / "artsniffer" / "analysis" / "cached_image.py"
    )
    allowed_modules = {
        "pathlib",
        "artsniffer.analysis.artwork",
        "artsniffer.analysis.image_analyser",
        "artsniffer.persistence.analysis_cache",
    }

    for node in ast.walk(ast.parse(module_path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            assert node.module is not None
            modules = [node.module]
        else:
            continue
        for module in modules:
            assert module in allowed_modules, f"Unexpected dependency: {module}"
