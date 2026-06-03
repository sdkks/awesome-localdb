"""
Recipe: Multimodal Storage with Hybrid Query
Database: LanceDB
Description: Demonstrates storing text alongside embeddings and metadata,
             then performing a hybrid query that combines vector search
             with structured filtering.

Usage: python src/recipe_multimodal_storage.py
"""

import os
import tempfile

import lancedb
import numpy as np


def main():
    # 1. Setup -- connect to a temporary LanceDB database
    tmpdir = tempfile.mkdtemp(prefix="lancedb_multimodal_")
    db_path = os.path.join(tmpdir, "multimodal.lance")
    db = lancedb.connect(db_path)

    # 2. Write -- store text, embeddings, and metadata
    dim = 64
    rng = np.random.default_rng(99)

    documents = [
        {
            "doc_id": "doc_001",
            "text": "LanceDB is an embedded vector database for multimodal AI.",
            "embedding": rng.normal(size=dim).tolist(),
            "source": "docs",
            "year": 2024,
            "tags": "vector,database,ai",
        },
        {
            "doc_id": "doc_002",
            "text": "PyTorch is a machine learning framework for deep learning.",
            "embedding": rng.normal(size=dim).tolist(),
            "source": "docs",
            "year": 2024,
            "tags": "ml,framework,pytorch",
        },
        {
            "doc_id": "doc_003",
            "text": "DuckDB is an in-process OLAP database for analytics.",
            "embedding": rng.normal(size=dim).tolist(),
            "source": "blog",
            "year": 2023,
            "tags": "olap,analytics,database",
        },
        {
            "doc_id": "doc_004",
            "text": "Embedded databases run inside the application process.",
            "embedding": rng.normal(size=dim).tolist(),
            "source": "blog",
            "year": 2023,
            "tags": "database,embedded",
        },
        {
            "doc_id": "doc_005",
            "text": "Vector search enables semantic similarity queries over text.",
            "embedding": rng.normal(size=dim).tolist(),
            "source": "docs",
            "year": 2024,
            "tags": "vector,search,semantic",
        },
    ]

    table = db.create_table("knowledge_base", data=documents, mode="overwrite")
    print(f"Created table 'knowledge_base' with {table.count_rows()} rows")

    # 3. Read -- hybrid query: vector search + metadata filter
    # Query vector roughly corresponding to "database storage"
    query_embedding = rng.normal(size=dim).tolist()

    # Vector search only (no filter)
    print("\nVector search (no filter):")
    results = table.search(query_embedding).limit(3).to_pandas()
    for _, row in results.iterrows():
        print(f"  {row['doc_id']}: {row['text'][:60]}... (dist: {row['_distance']:.4f})")

    # Hybrid: vector search with structured filter (source = "docs")
    print("\nHybrid query (vector + source='docs'):")
    filtered = (
        table.search(query_embedding)
        .where("source = 'docs'", prefilter=True)
        .limit(3)
        .to_pandas()
    )
    for _, row in filtered.iterrows():
        print(f"  {row['doc_id']}: {row['text'][:60]}... (dist: {row['_distance']:.4f})")

    # Hybrid: vector search with range filter (year >= 2024)
    print("\nHybrid query (vector + year >= 2024):")
    recent = (
        table.search(query_embedding)
        .where("year >= 2024", prefilter=True)
        .limit(3)
        .to_pandas()
    )
    for _, row in recent.iterrows():
        print(f"  {row['doc_id']}: {row['text'][:60]}... (dist: {row['_distance']:.4f})")

    # 4. Cleanup
    import shutil

    shutil.rmtree(tmpdir, ignore_errors=True)
    print(f"\nCleaned up {tmpdir}")


if __name__ == "__main__":
    main()
