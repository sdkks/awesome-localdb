"""
Recipe: Vector Search with Metadata Filtering
Database: LanceDB
Description: Demonstrates creating a table with embeddings, performing vector
             similarity search, and filtering results by metadata columns.

Usage: python src/recipe_vector_search.py
"""

import os
import tempfile

import lancedb
import numpy as np


def main():
    # 1. Setup -- connect to a temporary LanceDB database
    tmpdir = tempfile.mkdtemp(prefix="lancedb_recipe_")
    db_path = os.path.join(tmpdir, "demo.lance")
    db = lancedb.connect(db_path)

    # 2. Write -- create a table with embeddings and metadata
    dim = 128
    num_records = 100
    rng = np.random.default_rng(42)

    data = []
    for i in range(num_records):
        data.append(
            {
                "id": i,
                "vector": rng.normal(size=dim).tolist(),
                "category": rng.choice(["news", "sports", "tech"]),
                "score": float(rng.integers(0, 100)),
            }
        )

    table = db.create_table("articles", data=data, mode="overwrite")
    print(f"Created table 'articles' with {table.count_rows()} rows")

    # 3. Read -- vector search with metadata filtering
    query_vector = rng.normal(size=dim).tolist()

    # Basic vector search (pure similarity, no filter)
    results = table.search(query_vector).limit(5).to_pandas()
    print("\nTop 5 vector search results:")
    print(results[["id", "category", "score", "_distance"]])

    # Vector search with metadata filter (only "tech" category)
    filtered = (
        table.search(query_vector)
        .where("category = 'tech'", prefilter=True)
        .limit(5)
        .to_pandas()
    )
    print("\nTop 5 results filtered to 'tech' category:")
    print(filtered[["id", "category", "score", "_distance"]])

    # 4. Cleanup
    import shutil

    shutil.rmtree(tmpdir, ignore_errors=True)
    print(f"\nCleaned up {tmpdir}")


if __name__ == "__main__":
    main()
