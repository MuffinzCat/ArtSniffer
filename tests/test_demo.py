"""Tests for the local synthetic recommendation demo."""

import pytest

from artsniffer.demo import main


def test_demo_prints_the_synthetic_recommendation(capsys: pytest.CaptureFixture[str]) -> None:
    """The demo presents the same synthetic profile, score, and eligibility result."""
    main()
    captured = capsys.readouterr()

    assert captured.out == (
        "ArtSniffer local recommendation demo\n"
        "\n"
        "Profile: Muffin\n"
        "Artwork: candidate-001\n"
        "Score: 0.9982\n"
        "Eligible: True\n"
        "Reason: eligible\n"
    )
    assert captured.err == ""
