"""Tests for recipe_graph_cypher.py"""

from src.recipe_graph_cypher import main


def test_recipe_runs_without_error():
    """The recipe should execute without raising an exception."""
    main()


def test_recipe_produces_expected_output(capsys):
    """The recipe should output expected graph traversal results."""
    main()
    captured = capsys.readouterr()

    # Should contain all section headers
    assert "All People" in captured.out
    assert "Who Knows Whom" in captured.out
    assert "Friends of Alice" in captured.out
    assert "People Who Know Someone Alice Knows" in captured.out

    # Should contain expected node names in output
    assert "Alice" in captured.out
    assert "Bob" in captured.out
    assert "Carol" in captured.out
    assert "Dan" in captured.out

    # Should contain relationship details
    assert "knows" in captured.out

    # Should contain friend-of-a-friend result (Dan is a friend of both Carol and Bob who Alice knows)
    assert "Dan" in captured.out

    # Should end with Done
    assert "Done." in captured.out
