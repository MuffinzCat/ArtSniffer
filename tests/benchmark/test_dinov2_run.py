"""Offline runner tests using temporary manifests and synthetic embeddings only."""

import json
from pathlib import Path

import pytest

import artsniffer.benchmark.dinov2_run as runner
from artsniffer.analysis.artwork import ArtworkAnalysis


@pytest.fixture
def inference_calls(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, Path]]:
    """Replace the analyser before construction; never open images or load a model."""
    calls: list[tuple[str, Path]] = []

    class FakeAnalyser:
        model_id = "synthetic-model"

        def analyse(self, artwork_id: str, image_path: Path) -> ArtworkAnalysis:
            calls.append((artwork_id, image_path))
            embeddings = {
                "query-a": (1.0, 0.0),
                "query-b": (0.0, 1.0),
                "strong": (1.0, 0.0),
                "weak": (-1.0, 0.0),
            }
            return ArtworkAnalysis(artwork_id, self.model_id, embeddings[artwork_id])

    monkeypatch.setattr(runner, "DinoV2ImageAnalyser", FakeAnalyser)
    return calls


def _write_manifest(path: Path, comparisons: tuple[tuple[str, str, str], ...]) -> None:
    """Write metadata referring to nonexistent images, never real artwork."""
    images = "".join(
        f'[[images]]\nartwork_id = "{artwork_id}"\npath = "private/{artwork_id}.png"\n'
        for artwork_id in ("query-a", "query-b", "strong", "weak")
    )
    comparison_data = "".join(
        f'[[comparisons]]\nquery_artwork_id = "{query}"\n'
        f'strong_expected_match_id = "{strong}"\nweak_expected_match_id = "{weak}"\n'
        for query, strong, weak in comparisons
    )
    path.write_text(images + comparison_data, encoding="utf-8")


def test_runner_exports_one_path_free_result_per_manifest_query(
    tmp_path: Path,
    inference_calls: list[tuple[str, Path]],
    capsys: pytest.CaptureFixture[str],
) -> None:
    dataset_path = tmp_path / "synthetic.toml"
    results_directory = tmp_path / "reports"
    comparisons = (("query-b", "weak", "strong"), ("query-a", "strong", "weak"))
    _write_manifest(dataset_path, comparisons)

    runner.main(dataset_path, results_directory)

    assert inference_calls == [
        (artwork_id, tmp_path / "private" / f"{artwork_id}.png")
        for artwork_id in ("query-a", "query-b", "strong", "weak")
    ]
    assert sorted(path.name for path in results_directory.iterdir()) == [
        "query-a.json",
        "query-b.json",
    ]
    for query_id, strong_id, weak_id in comparisons:
        exported = (results_directory / f"{query_id}.json").read_text(encoding="utf-8")
        result = json.loads(exported)
        assert result["model_id"] == "synthetic-model"
        assert result["query_artwork_id"] == query_id
        assert result["embedding_dimensions"] == 2
        assert result["separation"]["strong_expected_match_id"] == strong_id
        assert result["separation"]["weak_expected_match_id"] == weak_id
        assert len(result["matches"]) == 3
        assert query_id not in [match["artwork_id"] for match in result["matches"]]
        assert "private" not in exported
        assert str(tmp_path) not in exported
        assert ".png" not in exported
    output = capsys.readouterr().out
    assert output.index("Query: query-b") < output.index("Query: query-a")
    assert (
        json.loads((results_directory / "query-a.json").read_text())["separation"]["value"] == 2.0
    )
    assert (
        json.loads((results_directory / "query-b.json").read_text())["separation"]["value"] == 0.0
    )


def test_runner_with_empty_comparisons_does_not_run_inference(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dataset_path = tmp_path / "synthetic.toml"
    dataset_path.write_text("images = []\ncomparisons = []\n", encoding="utf-8")
    results_directory = tmp_path / "reports"

    def unexpected_analyser() -> None:
        pytest.fail("Empty comparisons must not construct the real analyser.")

    monkeypatch.setattr(runner, "DinoV2ImageAnalyser", unexpected_analyser)

    runner.main(dataset_path, results_directory)

    assert not results_directory.exists()


def test_runner_reports_missing_query(
    tmp_path: Path, inference_calls: list[tuple[str, Path]]
) -> None:
    dataset_path = tmp_path / "synthetic.toml"
    _write_manifest(dataset_path, (("missing-query", "strong", "weak"),))
    results_directory = tmp_path / "reports"

    with pytest.raises(ValueError) as error:
        runner.main(dataset_path, results_directory)

    assert str(error.value) == (
        "Query artwork 'missing-query' was not found in the benchmark dataset."
    )
    assert list(results_directory.iterdir()) == []


@pytest.mark.parametrize("second_query_id", ["query-a", "QUERY-A"])
def test_runner_rejects_duplicate_query_outputs(
    tmp_path: Path, inference_calls: list[tuple[str, Path]], second_query_id: str
) -> None:
    dataset_path = tmp_path / "synthetic.toml"
    _write_manifest(
        dataset_path, (("query-a", "strong", "weak"), (second_query_id, "weak", "strong"))
    )
    results_directory = tmp_path / "reports"

    with pytest.raises(ValueError) as error:
        runner.main(dataset_path, results_directory)

    assert str(error.value) == "Comparison query artwork IDs must be unique."
    assert inference_calls == []
    assert not results_directory.exists()


@pytest.mark.parametrize("query_id", ["../escape", "/absolute", "C:escape", "NUL", ""])
def test_runner_rejects_unsafe_output_query_ids(
    tmp_path: Path, inference_calls: list[tuple[str, Path]], query_id: str
) -> None:
    dataset_path = tmp_path / "synthetic.toml"
    _write_manifest(dataset_path, ((query_id, "strong", "weak"),))
    results_directory = tmp_path / "reports"

    with pytest.raises(ValueError) as error:
        runner.main(dataset_path, results_directory)

    assert str(error.value) == "Comparison query artwork IDs must be safe filenames."
    assert inference_calls == []
    assert not results_directory.exists()
