"""Tests for recipe_datalog_queries.py"""

from src.recipe_datalog_queries import main


def test_recipe_runs_without_error():
    """The recipe should execute without raising an exception."""
    main()


def test_recipe_produces_expected_output(capsys):
    """The recipe should output query results from each section."""
    main()
    captured = capsys.readouterr()

    # Should contain all section headers
    assert "People in NYC" in captured.out
    assert "Friends Where Both Over 25" in captured.out
    assert "Friend Count" in captured.out
    assert "All Reachable Connections" in captured.out
    assert "Connections Within 2 Hops" in captured.out

    # Should contain expected person names
    assert "Alice" in captured.out
    assert "Bob" in captured.out
    assert "Carol" in captured.out
    assert "Dan" in captured.out
    assert "Eve" in captured.out
    assert "Frank" in captured.out

    # Alice, Carol, Frank are in NYC (age shown)
    assert "age 30" in captured.out  # Alice
    assert "age 28" in captured.out  # Carol
    assert "age 40" in captured.out  # Frank

    # Should contain graph traversal output
    assert "Alice -> Bob" in captured.out
    assert "Alice -> Carol" in captured.out

    # Should end with Done
    assert "Done." in captured.out
