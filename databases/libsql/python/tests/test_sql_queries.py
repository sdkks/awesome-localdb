"""Tests for recipe_sql_queries.py"""

import libsql_experimental as libsql
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from recipe_sql_queries import main


def test_recipe_runs_without_error():
    """The recipe should execute without raising an exception."""
    main()


def test_recipe_crud_operations_in_memory():
    """Verify CRUD operations work correctly on an in-memory database."""
    db = libsql.connect(":memory:")
    db.execute("PRAGMA foreign_keys = ON")

    # Create
    db.execute(
        "CREATE TABLE books (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, author TEXT NOT NULL)"
    )

    # Insert
    db.execute("INSERT INTO books (title, author) VALUES (?, ?)", ("Test Book", "Test Author"))
    assert db.execute("SELECT COUNT(*) FROM books").fetchone()[0] == 1

    # Update
    db.execute("UPDATE books SET author = ? WHERE title = ?", ("Updated Author", "Test Book"))
    author = db.execute("SELECT author FROM books WHERE title = ?", ("Test Book",)).fetchone()[0]
    assert author == "Updated Author"

    # Delete
    db.execute("DELETE FROM books WHERE title = ?", ("Test Book",))
    assert db.execute("SELECT COUNT(*) FROM books").fetchone()[0] == 0

    db.close()
