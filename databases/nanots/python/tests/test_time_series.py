"""Tests for recipe_time_series.py"""

import pytest

from src.recipe_time_series import main


def test_recipe_runs_without_error():
    """The recipe should execute without raising an exception."""
    try:
        import nanots  # noqa: F401
    except ImportError:
        pytest.skip("nanots package not installed")
    main()


def test_recipe_produces_expected_output(capsys):
    """The recipe should output time-series sections and expected data."""
    try:
        import nanots  # noqa: F401
    except ImportError:
        pytest.skip("nanots package not installed")

    main()
    captured = capsys.readouterr()

    # Should contain section headers
    assert "Allocating database" in captured.out
    assert "Writing temperature data" in captured.out
    assert "Writing humidity data" in captured.out
    assert "Reading temperature range" in captured.out
    assert "Iterator: seek to midpoint" in captured.out
    assert "Stream discovery" in captured.out

    # Should contain sensor data in output
    assert "temp-01" in captured.out
    assert "hum-01" in captured.out

    # Should end with Done
    assert "Done." in captured.out
