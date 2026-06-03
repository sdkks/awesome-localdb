"""
Recipe: Vector Search with sqlite-vec
Database: sqlite-vec
Description: Demonstrates creating a vector table, inserting embeddings,
             and performing exact KNN vector similarity search.

Usage: python src/recipe_vector_search.py
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

    # Verify the extension loaded correctly
    version = db.execute("SELECT vec_version()").fetchone()[0]
    print(f"sqlite-vec version: {version}")

    # 2. Write -- create a virtual table for 4-dimensional float vectors
    db.execute("CREATE VIRTUAL TABLE items USING vec0(embedding float[4])")

    num_records = 100
    vectors = []
    for i in range(num_records):
        # Simulated embeddings (cyclic for reproducibility)
        v = [(i * 0.1 + j * 0.03) % 1.0 for j in range(4)]
        vectors.append(v)

    for v in vectors:
        db.execute(
            "INSERT INTO items(embedding) VALUES (?)",
            [serialize_float32(v)],
        )
    print(f"Inserted {num_records} vectors into 'items'")

    # 3. Read -- exact KNN vector search
    query = serialize_float32([0.15, 0.25, 0.35, 0.45])
    results = db.execute(
        """
        SELECT rowid, distance
        FROM items
        WHERE embedding MATCH ?
        ORDER BY distance
        LIMIT 5
        """,
        [query],
    ).fetchall()

    print("\nTop 5 KNN results:")
    for rowid, distance in results:
        print(f"  rowid={rowid}, distance={distance:.4f}")
        print(f"    vector={vectors[rowid - 1]}")

    # 4. Cleanup
    db.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
