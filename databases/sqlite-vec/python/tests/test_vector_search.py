"""Tests for recipe_vector_search.py"""

import sqlite3

import sqlite_vec
from sqlite_vec import serialize_float32

from src.recipe_vector_search import main


def test_recipe_runs_without_error():
    """The recipe should execute without raising an exception."""
    main()


def test_create_table_and_search():
    """Verify table creation, vector insertion, and KNN search return expected results."""
    db = sqlite3.connect(":memory:")
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    db.enable_load_extension(False)

    db.execute("CREATE VIRTUAL TABLE items USING vec0(embedding float[4])")

    vectors = [[0.1 * i, 0.2 * i, 0.3 * i, 0.4 * i] for i in range(1, 21)]
    for v in vectors:
        db.execute("INSERT INTO items(embedding) VALUES (?)", [serialize_float32(v)])

    query = serialize_float32([0.15, 0.25, 0.35, 0.45])
    results = db.execute(
        """
        SELECT rowid, distance
        FROM items
        WHERE embedding MATCH ?
        ORDER BY distance
        LIMIT 3
        """,
        [query],
    ).fetchall()

    assert len(results) == 3
    for rowid, distance in results:
        assert isinstance(rowid, int)
        assert isinstance(distance, float)

    db.close()


def test_vector_search_ordering():
    """Results should be ordered by ascending distance."""
    db = sqlite3.connect(":memory:")
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    db.enable_load_extension(False)

    db.execute("CREATE VIRTUAL TABLE points USING vec0(embedding float[2])")

    # Insert vectors at varying distances from origin
    vecs = [
        [0.0, 0.0],   # distance 0
        [1.0, 0.0],   # distance 1
        [0.0, 1.0],   # distance 1
        [2.0, 0.0],   # distance 2
    ]
    for v in vecs:
        db.execute("INSERT INTO points(embedding) VALUES (?)", [serialize_float32(v)])

    # Query near origin
    query = serialize_float32([0.0, 0.0])
    results = db.execute(
        """
        SELECT rowid, distance
        FROM points
        WHERE embedding MATCH ?
        ORDER BY distance
        LIMIT 4
        """,
        [query],
    ).fetchall()

    assert len(results) == 4
    distances = [d for _, d in results]
    # First result should be closest (lowest distance)
    assert distances[0] < 0.01  # near zero
    assert distances == sorted(distances)

    db.close()
