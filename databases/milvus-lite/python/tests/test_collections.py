"""Tests for recipe_collections.py"""

import os
import tempfile

import numpy as np
from pymilvus import MilvusClient

from src.recipe_collections import main


def test_recipe_runs_without_error():
    """The recipe should execute without raising an exception."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        try:
            main()
        finally:
            os.chdir(original_cwd)


def test_create_list_drop_collections():
    """Verify collection CRUD: create, list, describe, has, and drop."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        client = MilvusClient(db_path)

        prefix = "test_crud_"
        alpha_name = f"{prefix}alpha"
        beta_name = f"{prefix}beta"
        gamma_name = f"{prefix}gamma"

        client.create_collection(collection_name=alpha_name, dimension=32)
        client.create_collection(collection_name=beta_name, dimension=32)

        collections = client.list_collections()
        assert alpha_name in collections
        assert beta_name in collections

        # has_collection check
        assert client.has_collection(beta_name) is True
        assert client.has_collection(gamma_name) is False

        # Create gamma
        client.create_collection(collection_name=gamma_name, dimension=32)
        assert client.has_collection(gamma_name) is True
        collections = client.list_collections()
        assert gamma_name in collections

        # Describe a collection
        desc = client.describe_collection(alpha_name)
        assert desc["collection_name"] == alpha_name
        assert any(f["name"] == "vector" for f in desc["fields"])

        # Drop and verify
        client.drop_collection(alpha_name)
        remaining = client.list_collections()
        assert alpha_name not in remaining
        assert beta_name in remaining
        assert gamma_name in remaining

        # Clean up
        client.drop_collection(beta_name)
        client.drop_collection(gamma_name)


def test_collection_stats_after_insert():
    """Verify collection stats reflect row count after insertion."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        client = MilvusClient(db_path)

        client.create_collection(collection_name="count_test", dimension=16)

        dim = 16
        n = 42
        rng = np.random.default_rng(1)

        data = [
            {"id": i, "vector": rng.normal(size=dim).tolist()}
            for i in range(n)
        ]
        client.insert("count_test", data)

        stats = client.get_collection_stats("count_test")
        assert stats["row_count"] == n

        client.drop_collection("count_test")


def test_describe_empty_collection():
    """describe_collection on an empty collection should return field schema."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        client = MilvusClient(db_path)

        client.create_collection(collection_name="empty", dimension=8)
        desc = client.describe_collection("empty")
        assert desc["collection_name"] == "empty"
        assert "fields" in desc
        assert "auto_id" in desc

        client.drop_collection("empty")
