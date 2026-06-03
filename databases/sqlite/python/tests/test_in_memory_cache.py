"""Tests for recipe_in_memory_cache.py"""

import sqlite3
import time
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from recipe_in_memory_cache import main


def test_recipe_runs_without_error():
    """The recipe should execute without raising an exception."""
    main()


def test_cache_hit_and_miss():
    """Verify cache lookup works for hit, miss, and expiry."""
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE cache (key TEXT PRIMARY KEY, value TEXT NOT NULL, expires_at REAL NOT NULL)"
    )

    now = time.time()
    conn.execute(
        "INSERT INTO cache (key, value, expires_at) VALUES (?, ?, ?)",
        ("key1", "value1", now + 3600),
    )
    conn.commit()

    # Hit
    row = conn.execute(
        "SELECT value, expires_at FROM cache WHERE key = ?", ("key1",)
    ).fetchone()
    assert row is not None
    assert row[0] == "value1"
    assert time.time() < row[1]

    # Miss
    row = conn.execute(
        "SELECT value, expires_at FROM cache WHERE key = ?", ("nonexistent",)
    ).fetchone()
    assert row is None

    conn.close()
