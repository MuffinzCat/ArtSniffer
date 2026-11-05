"""Tests for the ArtSniffer application entry point."""

import pytest

from artsniffer import main


def test_main_prints_greeting(capsys: pytest.CaptureFixture[str]) -> None:
    """The application entry point should print its greeting exactly once."""

    main()
    captured = capsys.readouterr()

    assert captured.out == "Hello from artsniffer!\n"
