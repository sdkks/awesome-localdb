"""Tests for recipe_graph_traversal.py"""

from src.recipe_graph_traversal import main


def test_recipe_runs_without_error():
    """The recipe should execute without raising an exception."""
    main()


def test_recipe_produces_expected_output(capsys):
    """The recipe should output graph traversal results."""
    main()
    captured = capsys.readouterr()

    # Should contain all section headers
    assert "Who Follows Whom" in captured.out
    assert "Recipes and Their Cooks" in captured.out
    assert "People Who Cooked the Same Recipes as Alice" in captured.out
    assert "Ingredients by Recipe" in captured.out

    # Should contain expected node names in output
    assert "Alice" in captured.out
    assert "Bob" in captured.out
    assert "Carol" in captured.out
    assert "Dan" in captured.out

    # Should contain recipe titles
    assert "Spaghetti Bolognese" in captured.out
    assert "Chicken Curry" in captured.out
    assert "Avocado Toast" in captured.out

    # Should contain ingredient names
    assert "Pasta" in captured.out
    assert "Tomato Sauce" in captured.out
    assert "Chicken" in captured.out
    assert "Curry Powder" in captured.out
    assert "Avocado" in captured.out
    assert "Bread" in captured.out

    # Should end with Done
    assert "Done." in captured.out
