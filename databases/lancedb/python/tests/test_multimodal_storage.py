"""Tests for recipe_multimodal_storage.py"""

import os
import tempfile

import lancedb
import numpy as np

from src.recipe_multimodal_storage import main


def test_recipe_runs_without_error():
    """The recipe should execute without raising an exception."""
    main()


def test_multimodal_hybrid_query():
    """Hybrid query combining vector search and structured filter returns expected results."""
    tmpdir = tempfile.mkdtemp(prefix="lancedb_test_mm_")
    db_path = os.path.join(tmpdir, "test_mm.lance")
    db = lancedb.connect(db_path)

    dim = 32
    rng = np.random.default_rng(42)

    data = [
        {
            "id": i,
            "text": f"document {i}",
            "embedding": rng.normal(size=dim).tolist(),
            "source": "docs" if i % 2 == 0 else "blog",
            "year": 2023 + (i % 3),
        }
        for i in range(30)
    ]
    table = db.create_table("kb", data=data, mode="overwrite")
    assert table.count_rows() == 30

    query = rng.normal(size=dim).tolist()

    # Vector-only search
    all_results = table.search(query).limit(10).to_pandas()
    assert len(all_results) == 10

    # Hybrid: filter by source
    docs_results = (
        table.search(query)
        .where("source = 'docs'", prefilter=True)
        .limit(10)
        .to_pandas()
    )
    assert len(docs_results) > 0
    assert all(docs_results["source"] == "docs")

    # Hybrid: filter by year range
    year_results = (
        table.search(query)
        .where("year >= 2025", prefilter=True)
        .limit(10)
        .to_pandas()
    )
    assert all(year_results["year"] >= 2025)

    import shutil

    shutil.rmtree(tmpdir, ignore_errors=True)


def test_multimodal_text_and_embedding_stored():
    """Verify that text and embeddings are stored and retrievable."""
    tmpdir = tempfile.mkdtemp(prefix="lancedb_test_mm2_")
    db_path = os.path.join(tmpdir, "test_mm2.lance")
    db = lancedb.connect(db_path)

    dim = 16
    rng = np.random.default_rng(1)

    data = [
        {
            "id": 1,
            "text": "hello world",
            "embedding": rng.normal(size=dim).tolist(),
            "tag": "greeting",
        }
    ]
    table = db.create_table("entries", data=data, mode="overwrite")

    # Query without vector search to verify stored data
    query = rng.normal(size=dim).tolist()
    df = table.search(query).limit(5).to_pandas()
    assert len(df) == 1
    assert df.iloc[0]["text"] == "hello world"
    assert df.iloc[0]["tag"] == "greeting"
    assert len(df.iloc[0]["embedding"]) == dim

    import shutil

    shutil.rmtree(tmpdir, ignore_errors=True)
