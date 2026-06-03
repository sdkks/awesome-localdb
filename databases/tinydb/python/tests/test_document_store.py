"""Tests for recipe_document_store.py"""

from src.recipe_document_store import main


def test_recipe_runs_without_error():
    """The recipe should execute without raising an exception."""
    main()
