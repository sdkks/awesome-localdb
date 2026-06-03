"""Tests for recipe_graph_vector.py"""

from src.recipe_graph_vector import main


def test_recipe_runs_without_error():
    """The recipe should execute without raising an exception."""
    main()


def test_recipe_produces_expected_output(capsys):
    """The recipe should output graph traversal and vector search results."""
    main()
    captured = capsys.readouterr()

    # Should contain graph sections
    assert "Who does Alice know?" in captured.out
    assert "Where do Alice's friends live?" in captured.out
    assert "Who lives in London?" in captured.out
    assert "Who can Alice reach through friends?" in captured.out
    assert "Direct friends:" in captured.out
    assert "Friends of friends:" in captured.out

    # Should contain vector search section
    assert "Approximate vector similarity search" in captured.out

    # Should contain expected data
    assert "Bob" in captured.out
    assert "London" in captured.out

    # Should end with Done
    assert "Done." in captured.out
