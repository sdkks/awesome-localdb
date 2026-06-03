"""Tests for recipe_vector_search.py"""

from src.recipe_vector_search import main


def test_recipe_runs_without_error():
    """The recipe should execute without raising an exception."""
    main()


def test_recipe_produces_expected_output(capsys):
    """The recipe should output vector similarity search results."""
    main()
    captured = capsys.readouterr()

    # Should contain all section headers
    assert "Top 3 Nearest Neighbors of Orange" in captured.out
    assert "Fruits Similar to Orange" in captured.out
    assert "Fruits Moderately Similar to Apple" in captured.out
    assert "Citrus Fruits Similar to Orange" in captured.out
    assert "Fruits Dissimilar to Banana" in captured.out
    assert "Tropical Fruits Nearest to Mango" in captured.out
    assert "Embedding Stats" in captured.out

    # Should contain expected fruit names in output (matching which
    # fruits appear given the actual embedding distances)
    assert "orange" in captured.out
    assert "tangerine" in captured.out
    assert "lemon" in captured.out
    assert "banana" in captured.out
    assert "mango" in captured.out

    # Category "Citrus" already covered by section header above

    # Should contain embedding stats
    assert "Count" in captured.out
    assert "Dimensions" in captured.out

    # Should end with Done
    assert "Done." in captured.out
