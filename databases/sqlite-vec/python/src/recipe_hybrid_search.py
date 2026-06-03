"""
Recipe: Hybrid Search with sqlite-vec
Database: sqlite-vec
Description: Demonstrates vector similarity search combined with structured
             metadata filtering (hybrid search) using a separate metadata
             table joined with the vector virtual table.

Usage: python src/recipe_hybrid_search.py
"""

import sqlite3

import sqlite_vec
from sqlite_vec import serialize_float32


def main():
    # 1. Setup -- connect to an in-memory SQLite database
    db = sqlite3.connect(":memory:")
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    db.enable_load_extension(False)

    # 2. Schema -- vector virtual table + metadata table
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

    # 3. Write -- insert vectors and metadata
    categories = ["news", "sports", "tech", "science"]
    num_records = 40

    for i in range(num_records):
        # Simulated embeddings
        v = [(i * 0.05 + j * 0.07) % 1.0 for j in range(4)]
        db.execute(
            "INSERT INTO docs_vec(embedding) VALUES (?)",
            [serialize_float32(v)],
        )
        cat = categories[i % len(categories)]
        db.execute(
            "INSERT INTO docs_meta (id, title, category, year) VALUES (?, ?, ?, ?)",
            [i + 1, f"Document {i}", cat, 2023 + (i % 3)],
        )
    print(f"Inserted {num_records} documents with metadata")

    # 4. Read -- hybrid search: vector similarity + category filter
    query = serialize_float32([0.2, 0.3, 0.4, 0.5])

    # Pure vector search (no filter)
    vec_results = db.execute(
        """
        SELECT d.rowid, d.distance, m.title, m.category, m.year
        FROM docs_vec d
        JOIN docs_meta m ON d.rowid = m.id
        WHERE d.embedding MATCH ? AND k = 5
        ORDER BY d.distance
        """,
        [query],
    ).fetchall()

    print("\nTop 5 vector search results (no filter):")
    for rowid, distance, title, cat, year in vec_results:
        print(f"  rowid={rowid}, distance={distance:.4f}, {title}, cat={cat}, year={year}")

    # Hybrid search: vector + category filter ("tech" only)
    hybrid_results = db.execute(
        """
        SELECT d.rowid, d.distance, m.title, m.category, m.year
        FROM docs_vec d
        JOIN docs_meta m ON d.rowid = m.id
        WHERE d.embedding MATCH ? AND k = 5
          AND m.category = 'tech'
        ORDER BY d.distance
        """,
        [query],
    ).fetchall()

    print("\nTop 5 hybrid results (category='tech'):")
    for rowid, distance, title, cat, year in hybrid_results:
        print(f"  rowid={rowid}, distance={distance:.4f}, {title}, cat={cat}, year={year}")

    # Hybrid search: vector + year range filter
    year_results = db.execute(
        """
        SELECT d.rowid, d.distance, m.title, m.category, m.year
        FROM docs_vec d
        JOIN docs_meta m ON d.rowid = m.id
        WHERE d.embedding MATCH ? AND k = 5
          AND m.year >= 2025
        ORDER BY d.distance
        """,
        [query],
    ).fetchall()

    print("\nTop 5 hybrid results (year >= 2025):")
    for rowid, distance, title, cat, year in year_results:
        print(f"  rowid={rowid}, distance={distance:.4f}, {title}, cat={cat}, year={year}")

    # 5. Cleanup
    db.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
