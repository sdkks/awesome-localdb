"""Tests for recipe_olap_query.py"""

from src.recipe_olap_query import main


def test_recipe_runs_without_error():
    """The recipe should execute without raising an exception."""
    main()


def test_recipe_produces_expected_aggregation(capsys):
    """The recipe should output GROUP BY and window function results."""
    main()
    captured = capsys.readouterr()

    # Should contain aggregation section headers
    assert "Sales by Category and Region" in captured.out
    assert "Sales Ranked Within Each Category" in captured.out
    assert "Running Total of Sales Over Time" in captured.out
    assert "Top Region per Category" in captured.out

    # Should contain expected category values in output
    assert "Electronics" in captured.out
    assert "Clothing" in captured.out
    assert "Groceries" in captured.out

    # Should have computed the running total and ranking
    assert "running_total" in captured.out
    assert "rank" in captured.out

    # Should end with Done
    assert "Done." in captured.out
