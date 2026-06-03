"""Tests for recipe_vector_search.py"""

import os
import tempfile

import numpy as np
from pymilvus import MilvusClient

from src.recipe_vector_search import main


def test_recipe_runs_without_error():
    """The recipe should execute without raising an exception."""
    # main() uses a relative path; run from a temp directory
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        try:
            main()
        finally:
            os.chdir(original_cwd)


def test_create_collection_and_search():
    """Verify collection creation, document count, and vector search return expected results."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        client = MilvusClient(db_path)

        dim = 64
        rng = np.random.default_rng(13)
        num_docs = 20

        client.create_collection(collection_name="test_docs", dimension=dim)

        data = [
            {
                "id": i,
                "vector": rng.normal(size=dim).tolist(),
                "text": f"Test document {i}",
                "kind": "a" if i < 10 else "b",
            }
            for i in range(num_docs)
        ]
        client.insert("test_docs", data)

        stats = client.get_collection_stats("test_docs")
        assert stats["row_count"] == num_docs

        query_vector = rng.normal(size=dim).tolist()
        results = client.search(
            collection_name="test_docs",
            data=[query_vector],
            limit=3,
            output_fields=["id"],
        )
        assert len(results[0]) == 3

        client.drop_collection("test_docs")


def test_vector_search_with_scalar_filter():
    """Vector search with scalar filter should return only matching rows."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        client = MilvusClient(db_path)

        dim = 32
        rng = np.random.default_rng(42)
        num_docs = 20

        client.create_collection(collection_name="test_filter", dimension=dim)

        data = [
            {
                "id": i,
                "vector": rng.normal(size=dim).tolist(),
                "color": "red" if i < 10 else "blue",
            }
            for i in range(num_docs)
        ]
        client.insert("test_filter", data)

        query_vector = rng.normal(size=dim).tolist()
        results = client.search(
            collection_name="test_filter",
            data=[query_vector],
            limit=10,
            filter="color == 'red'",
            output_fields=["color"],
        )
        # All returned entities should have color "red"
        for hit in results[0]:
            assert hit["entity"]["color"] == "red"

        client.drop_collection("test_filter")


def test_scalar_query_only():
    """Scalar-only query without vector should return matching rows by filter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        client = MilvusClient(db_path)

        dim = 16
        rng = np.random.default_rng(99)
        num_docs = 15

        client.create_collection(collection_name="test_scalar", dimension=dim)

        data = [
            {
                "id": i,
                "vector": rng.normal(size=dim).tolist(),
                "category": "a" if i < 5 else "b" if i < 10 else "c",
                "value": i * 10,
            }
            for i in range(num_docs)
        ]
        client.insert("test_scalar", data)

        rows = client.query(
            collection_name="test_scalar",
            filter="category == 'a'",
            output_fields=["category", "value"],
        )
        assert len(rows) == 5
        for row in rows:
            assert row["category"] == "a"

        client.drop_collection("test_scalar")
