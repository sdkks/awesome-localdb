"""Tests for recipe_hybrid_search.py"""

import sqlite3

import sqlite_vec
from sqlite_vec import serialize_float32

from src.recipe_hybrid_search import main


def test_recipe_runs_without_error():
    """The recipe should execute without raising an exception."""
    main()


def test_hybrid_search_category_filter():
    """Hybrid query combining vector search and category filter returns only matching rows."""
    db = sqlite3.connect(":memory:")
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    db.enable_load_extension(False)

    db.execute("CREATE VIRTUAL TABLE docs_vec USING vec0(embedding float[4])")
    db.execute(
        """
        CREATE TABLE docs_meta (
            id INTEGER PRIMARY KEY,
            title TEXT,
            category TEXT,
            year INTEGER
        )
        """
    )

    # Insert 20 documents with metadata
    categories = ["news", "tech"]
    for i in range(20):
        v = [(i * 0.05 + j * 0.07) % 1.0 for j in range(4)]
        db.execute("INSERT INTO docs_vec(embedding) VALUES (?)", [serialize_float32(v)])
        cat = categories[i % 2]
        db.execute(
            "INSERT INTO docs_meta (id, title, category, year) VALUES (?, ?, ?, ?)",
            [i + 1, f"Doc {i}", cat, 2023 + (i % 3)],
        )

    query = serialize_float32([0.2, 0.3, 0.4, 0.5])
    results = db.execute(
        """
        SELECT d.rowid, d.distance, m.category
        FROM docs_vec d
        JOIN docs_meta m ON d.rowid = m.id
        WHERE d.embedding MATCH ? AND k = 10
          AND m.category = 'tech'
        ORDER BY d.distance
        """,
        [query],
    ).fetchall()

    assert len(results) > 0
    for _, _, cat in results:
        assert cat == "tech"

    db.close()


def test_hybrid_search_year_filter():
    """Hybrid query with year range filter should return only matching documents."""
    db = sqlite3.connect(":memory:")
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    db.enable_load_extension(False)

    db.execute("CREATE VIRTUAL TABLE docs_vec USING vec0(embedding float[4])")
    db.execute(
        """
        CREATE TABLE docs_meta (
            id INTEGER PRIMARY KEY,
            title TEXT,
            category TEXT,
            year INTEGER
        )
        """
    )

    for i in range(30):
        v = [(i * 0.03 + j * 0.11) % 1.0 for j in range(4)]
        db.execute("INSERT INTO docs_vec(embedding) VALUES (?)", [serialize_float32(v)])
        db.execute(
            "INSERT INTO docs_meta (id, title, category, year) VALUES (?, ?, ?, ?)",
            [i + 1, f"Doc {i}", "general", 2023 + (i % 4)],
        )

    query = serialize_float32([0.5, 0.5, 0.5, 0.5])
    results = db.execute(
        """
        SELECT d.rowid, d.distance, m.year
        FROM docs_vec d
        JOIN docs_meta m ON d.rowid = m.id
        WHERE d.embedding MATCH ? AND k = 10
          AND m.year >= 2026
        ORDER BY d.distance
        """,
        [query],
    ).fetchall()

    assert len(results) > 0
    for _, _, year in results:
        assert year >= 2026

    db.close()


def test_pure_vector_vs_hybrid_count():
    """Hybrid search with a filter should return fewer or equal results than pure vector search."""
    db = sqlite3.connect(":memory:")
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    db.enable_load_extension(False)

    db.execute("CREATE VIRTUAL TABLE items_vec USING vec0(embedding float[4])")
    db.execute("CREATE TABLE items_meta (id INTEGER PRIMARY KEY, kind TEXT)")

    for i in range(20):
        v = [(i * 0.05 + j * 0.07) % 1.0 for j in range(4)]
        db.execute("INSERT INTO items_vec(embedding) VALUES (?)", [serialize_float32(v)])
        db.execute(
            "INSERT INTO items_meta (id, kind) VALUES (?, ?)",
            [i + 1, "a" if i < 8 else "b"],
        )

    query = serialize_float32([0.1, 0.2, 0.3, 0.4])

    all_results = db.execute(
        """
        SELECT rowid FROM items_vec
        WHERE embedding MATCH ? AND k = 20
        ORDER BY distance
        """,
        [query],
    ).fetchall()

    filtered_results = db.execute(
        """
        SELECT v.rowid
        FROM items_vec v
        JOIN items_meta m ON v.rowid = m.id
        WHERE v.embedding MATCH ? AND k = 20
          AND m.kind = 'a'
        ORDER BY v.distance
        """,
        [query],
    ).fetchall()

    # Filtered results should be a subset (fewer or equal)
    assert len(filtered_results) <= len(all_results)
    assert len(filtered_results) > 0

    db.close()
