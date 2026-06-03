"""Tests for recipe_transactional_storage.py"""

import sqlite3
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from recipe_transactional_storage import main


def test_recipe_runs_without_error():
    """The recipe should execute without raising an exception."""
    # main() creates and cleans up its own database file
    main()


def test_recipe_crud_operations_in_memory():
    """Verify CRUD operations work correctly on an in-memory database."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")

    # Create
    conn.execute(
        "CREATE TABLE books (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, author TEXT NOT NULL)"
    )

    # Insert
    conn.execute("INSERT INTO books (title, author) VALUES (?, ?)", ("Test Book", "Test Author"))
    conn.commit()
    assert conn.execute("SELECT COUNT(*) FROM books").fetchone()[0] == 1

    # Update
    conn.execute("UPDATE books SET author = ? WHERE title = ?", ("Updated Author", "Test Book"))
    conn.commit()
    author = conn.execute("SELECT author FROM books WHERE title = ?", ("Test Book",)).fetchone()[0]
    assert author == "Updated Author"

    # Delete
    conn.execute("DELETE FROM books WHERE title = ?", ("Test Book",))
    conn.commit()
    assert conn.execute("SELECT COUNT(*) FROM books").fetchone()[0] == 0

    conn.close()
