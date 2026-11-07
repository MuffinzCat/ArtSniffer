"""Run local DINOv2 inference once and export each manifest-selected comparison.

Run with ``python -m artsniffer.benchmark.dinov2_run`` using the optional
benchmark-dinov2 dependencies. Model loading may download uncached model files.
"""

from pathlib import Path, PureWindowsPath

from artsniffer.analysis.dinov2_analyser import DinoV2ImageAnalyser
from artsniffer.benchmark.dataset import (
    load_benchmark_comparisons,
    load_benchmark_images,
)
from artsniffer.benchmark.results import build_benchmark_result
from artsniffer.benchmark.runner import benchmark_images


def main(
    dataset_path: Path = Path("benchmark-data") / "dataset.toml",
    results_directory: Path = Path("benchmark-data") / "results" / "dinov2-small",
) -> None:
    """Write query-named JSON reports in manifest order using stable artwork IDs.

    Query IDs must be unique ignoring case and safe filenames. Paths stay outside result JSON.
    Empty comparisons produce no reports and do not load the model or run inference.
    """
    images = load_benchmark_images(dataset_path)
    comparisons = load_benchmark_comparisons(dataset_path)
    if not comparisons:
        return
    query_ids = [comparison.query_artwork_id for comparison in comparisons]
    if len({query_id.casefold() for query_id in query_ids}) != len(query_ids):
        raise ValueError("Comparison query artwork IDs must be unique.")
    for query_id in query_ids:
        if (
            not query_id.strip()
            or any(character in '<>:"/\\|?*' or ord(character) < 32 for character in query_id)
            or PureWindowsPath(f"{query_id}.json").is_reserved()
        ):
            raise ValueError("Comparison query artwork IDs must be safe filenames.")

    analyser = DinoV2ImageAnalyser()
    analyses = benchmark_images(analyser, images)
    results_directory.mkdir(parents=True, exist_ok=True)

    for comparison in comparisons:
        query = None

        for analysis in analyses:
            if analysis.artwork_id == comparison.query_artwork_id:
                query = analysis
                break

        if query is None:
            raise ValueError(
                f"Query artwork {comparison.query_artwork_id!r} "
                "was not found in the benchmark dataset."
            )

        result = build_benchmark_result(
            query,
            analyses,
            separation_pair=(
                comparison.strong_expected_match_id,
                comparison.weak_expected_match_id,
            ),
        )

        result_path = results_directory / f"{comparison.query_artwork_id}.json"
        result_path.write_text(result.to_json(), encoding="utf-8")

        print(f"Model: {result.model_id}")
        print(f"Query: {result.query_artwork_id}")

        for match in result.matches:
            print(f"{match.artwork_id}: {match.similarity:.4f}")

        if result.separation is not None:
            print(f"Separation: {result.separation.value:.4f}")

        print(f"Saved: {result_path}")
        print()


if __name__ == "__main__":
    main()
