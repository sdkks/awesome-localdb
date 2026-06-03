"""
Recipe: Vector Similarity Search
Database: libSQL
Description: Demonstrates storing vector embeddings as BLOBs and computing
             cosine similarity between query and stored vectors using SQL.
             Uses libSQL (SQLite-compatible) arithmetic for distance computation.

Usage: python src/recipe_vector_search.py
"""

import libsql_experimental as libsql
import math
import os
import struct
import sys


def vector_to_blob(vec: list[float]) -> bytes:
    """Pack a list of floats into a BLOB of little-endian f64 values."""
    return struct.pack(f"<{len(vec)}d", *vec)


def blob_to_vector(blob: bytes) -> list[float]:
    """Unpack a BLOB of little-endian f64 values into a list of floats."""
    count = len(blob) // 8
    return list(struct.unpack(f"<{count}d", blob))


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def main() -> None:
    db_path = os.path.join(os.path.dirname(__file__), "..", "recipe_vectors.db")
    db_path = os.path.abspath(db_path)

    # ── 1. Setup ──────────────────────────────────────────────────────
    db = libsql.connect(db_path)
    db.execute("PRAGMA journal_mode=WAL")

    print(f"Connected to {db_path}")

    # ── 2. Schema ─────────────────────────────────────────────────────
    db.execute("""
        CREATE TABLE IF NOT EXISTS embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            vector BLOB NOT NULL,
            dimensions INTEGER NOT NULL
        )
    """)
    print("Table 'embeddings' ready.")

    # ── 3. Insert sample embeddings ───────────────────────────────────
    # Simulated embeddings for simple phrases (4-dimensional for demo)
    samples = [
        ("apple fruit", [0.8, 0.2, 0.1, 0.0]),
        ("banana fruit", [0.7, 0.3, 0.1, 0.1]),
        ("orange fruit", [0.9, 0.1, 0.2, 0.0]),
        ("car vehicle", [0.1, 0.8, 0.0, 0.2]),
        ("truck vehicle", [0.0, 0.9, 0.1, 0.2]),
        ("python programming", [0.2, 0.1, 0.9, 0.1]),
    ]

    try:
        for text, vec in samples:
            blob = vector_to_blob(vec)
            db.execute(
                "INSERT INTO embeddings (text, vector, dimensions) VALUES (?, ?, ?)",
                (text, blob, len(vec)),
            )
        print(f"Inserted {len(samples)} embeddings.")
    except Exception as e:
        print(f"Insert error: {e}", file=sys.stderr)

    # ── 4. Vector search by cosine similarity ─────────────────────────
    # Query: find texts most similar to "fruit" concept [0.85, 0.15, 0.1, 0.0]
    query_vec = [0.85, 0.15, 0.1, 0.0]

    print(f"\nQuery vector: {query_vec}")
    print("Top 3 most similar embeddings:")

    # Fetch all embeddings and compute similarity in Python
    # (libSQL can also compute via SQL arithmetic on unpacked BLOB fields)
    rows = db.execute(
        "SELECT id, text, vector FROM embeddings ORDER BY id"
    ).fetchall()

    results = []
    for row in rows:
        row_id, text, blob = row
        stored_vec = blob_to_vector(blob)
        sim = cosine_similarity(query_vec, stored_vec)
        results.append((row_id, text, sim))

    # Sort by similarity descending and display top 3
    results.sort(key=lambda x: x[2], reverse=True)

    for row_id, text, sim in results[:3]:
        bar = "#" * int(sim * 20)
        print(f"  [{row_id}] {text:<20s}  similarity={sim:.4f}  {bar}")

    # ── 5. Threshold filtering ────────────────────────────────────────
    threshold = 0.7
    print(f"\nResults above similarity threshold {threshold}:")
    matches = [r for r in results if r[2] >= threshold]
    if matches:
        for row_id, text, sim in matches:
            print(f"  [{row_id}] {text:<20s}  similarity={sim:.4f}")
    else:
        print("  (no results above threshold)")

    # ── 6. Cleanup ────────────────────────────────────────────────────
    db.close()
    os.remove(db_path)
    print(f"\nCleaned up {db_path}.")


if __name__ == "__main__":
    main()
