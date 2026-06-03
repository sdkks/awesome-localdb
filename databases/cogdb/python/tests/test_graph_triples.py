"""Tests for recipe_graph_triples.py"""

from src.recipe_graph_triples import main


def test_recipe_runs_without_error():
    """The recipe should execute without raising an exception."""
    main()


def test_recipe_produces_expected_output(capsys):
    """The recipe should output graph traversal results."""
    main()
    captured = capsys.readouterr()

    # Should contain all section headers
    assert "Who Alice Follows" in captured.out
    assert "Who Follows Dan" in captured.out
    assert "Active Users" in captured.out
    assert "People Who Cook Italian" in captured.out
    assert "Friends of Friends" in captured.out
    assert "Count of Alice's Follows" in captured.out
    assert "Bidirectional Connections to Dan" in captured.out

    # Should contain expected vertex names in output
    assert "alice" in captured.out
    assert "bob" in captured.out
    assert "carol" in captured.out
    assert "dan" in captured.out
    assert "eve" in captured.out
    assert "frank" in captured.out

    # Should contain cuisine mentions (capitalized as in output)
    assert "Italian" in captured.out

    # Should end with Done
    assert "Done." in captured.out
