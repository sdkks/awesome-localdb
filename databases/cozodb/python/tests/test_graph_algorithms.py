"""Tests for recipe_graph_algorithms.py"""

from src.recipe_graph_algorithms import main


def test_recipe_runs_without_error():
    """The recipe should execute without raising an exception."""
    main()


def test_recipe_produces_expected_output(capsys):
    """The recipe should output graph analytics results from each section."""
    main()
    captured = capsys.readouterr()

    # Should contain all section headers
    assert "Social Graph" in captured.out
    assert "Shortest Paths from Alice" in captured.out
    assert "Degree Centrality" in captured.out
    assert "Cross-Department Interactions" in captured.out
    assert "Most Influential" in captured.out

    # Should contain all person names
    for name in ["Alice", "Bob", "Carol", "Dan", "Eve", "Frank", "Grace", "Hank"]:
        assert name in captured.out

    # Should contain department names
    for dept in ["Engineering", "Design", "Marketing"]:
        assert dept in captured.out

    # Should contain graph analytics terminology
    assert "hop" in captured.out
    assert "degree" in captured.out
    assert "score" in captured.out

    # Should end with Done
    assert "Done." in captured.out
