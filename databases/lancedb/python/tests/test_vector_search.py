"""Tests for recipe_vector_search.py"""

import os
import tempfile

import lancedb
import numpy as np

from src.recipe_vector_search import main


def test_recipe_runs_without_error():
    """The recipe should execute without raising an exception."""
    main()


def test_create_table_and_search():
    """Verify table creation, row count, and vector search return expected results."""
    tmpdir = tempfile.mkdtemp(prefix="lancedb_test_")
    db_path = os.path.join(tmpdir, "test.lance")
    db = lancedb.connect(db_path)

    dim = 32
    rng = np.random.default_rng(7)

    data = [
        {"id": i, "vector": rng.normal(size=dim).tolist(), "category": "test"}
        for i in range(20)
    ]
    table = db.create_table("items", data=data, mode="overwrite")
    assert table.count_rows() == 20

    query = rng.normal(size=dim).tolist()
    results = table.search(query).limit(3).to_pandas()
    assert len(results) == 3
    assert "id" in results.columns
    assert "_distance" in results.columns

    import shutil

    shutil.rmtree(tmpdir, ignore_errors=True)


def test_vector_search_with_filter():
    """Vector search with metadata prefilter should return only matching rows."""
    tmpdir = tempfile.mkdtemp(prefix="lancedb_test_")
    db_path = os.path.join(tmpdir, "test_filter.lance")
    db = lancedb.connect(db_path)

    dim = 16
    rng = np.random.default_rng(13)

    data = []
    for i in range(10):
        data.append(
            {
                "id": i,
                "vector": rng.normal(size=dim).tolist(),
                "kind": "a" if i < 5 else "b",
            }
        )
    table = db.create_table("mixed", data=data, mode="overwrite")

    query = rng.normal(size=dim).tolist()
    results = (
        table.search(query).where("kind = 'a'", prefilter=True).limit(10).to_pandas()
    )
    assert all(results["kind"] == "a")

    import shutil

    shutil.rmtree(tmpdir, ignore_errors=True)
