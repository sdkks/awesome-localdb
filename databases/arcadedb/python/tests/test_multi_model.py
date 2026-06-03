"""Tests for recipe_multi_model.py"""

import sys
from pathlib import Path

# Ensure the src directory is on the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from recipe_multi_model import main


def test_recipe_runs_without_error():
    """The recipe should execute without raising an exception."""
    main()


def test_recipe_produces_expected_output(capsys):
    """The recipe should output multi-model operation results."""
    main()
    captured = capsys.readouterr()

    # Graph section
    assert "Graph: People Alice knows" in captured.out
    assert "Alice knows" in captured.out
    assert "Graph: Two-hop from Alice" in captured.out
    assert "friend_of_friend" in captured.out

    # Document section
    assert "Documents: All articles" in captured.out
    assert "Graph Databases 101" in captured.out
    assert "Vector Search Explained" in captured.out

    # Vector section
    assert "Vector: Similarity search" in captured.out

    # Time-series section
    assert "Time-series: Sensor readings" in captured.out
    assert "sensor-1" in captured.out

    # Should end with Done
    assert "Done." in captured.out
