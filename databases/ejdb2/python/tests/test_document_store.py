"""Tests for recipe_document_store.py"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.recipe_document_store import main


def test_recipe_imports():
    """Verify the recipe module can be imported without errors."""
    from src.recipe_document_store import _load_library

    # Just verify the module is importable; library loading is tested separately
    assert callable(_load_library)
