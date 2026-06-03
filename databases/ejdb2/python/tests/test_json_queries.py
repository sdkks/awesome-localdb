"""Tests for recipe_json_queries.py"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.recipe_json_queries import main


def test_recipe_imports():
    """Verify the recipe module can be imported without errors."""
    from src.recipe_json_queries import _load_library

    # Just verify the module is importable; library loading is tested separately
    assert callable(_load_library)
