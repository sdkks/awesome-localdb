"""Tests for recipe_config_database.py"""

from src.recipe_config_database import main


def test_recipe_runs_without_error():
    """The recipe should execute without raising an exception."""
    main()
