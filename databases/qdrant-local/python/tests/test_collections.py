"""Tests for recipe_collections.py"""

import numpy as np

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from src.recipe_collections import main


def test_recipe_runs_without_error():
    """The recipe should execute without raising an exception."""
    main()


def test_create_list_delete_collections():
    """Verify collection CRUD: create, list, exists check, and delete."""
    client = QdrantClient(location=":memory:")

    prefix = "test_crud_"
    alpha_name = f"{prefix}alpha"
    beta_name = f"{prefix}beta"
    gamma_name = f"{prefix}gamma"

    client.create_collection(
        collection_name=alpha_name,
        vectors_config=VectorParams(size=16, distance=Distance.COSINE),
    )
    client.create_collection(
        collection_name=beta_name,
        vectors_config=VectorParams(size=16, distance=Distance.COSINE),
    )

    collections = client.get_collections()
    names = {c.name for c in collections.collections}
    assert alpha_name in names
    assert beta_name in names

    assert client.collection_exists(collection_name=beta_name) is True
    assert client.collection_exists(collection_name=gamma_name) is False

    client.create_collection(
        collection_name=gamma_name,
        vectors_config=VectorParams(size=16, distance=Distance.COSINE),
    )
    names = {c.name for c in client.get_collections().collections}
    assert gamma_name in names

    client.delete_collection(collection_name=alpha_name)
    remaining = {c.name for c in client.get_collections().collections}
    assert alpha_name not in remaining
    assert beta_name in remaining
    assert gamma_name in remaining

    client.delete_collection(collection_name=beta_name)
    client.delete_collection(collection_name=gamma_name)

    client.close()


def test_collection_point_count():
    """Verify collection point count after upserting documents."""
    client = QdrantClient(location=":memory:")

    dim = 16
    n = 42
    rng = np.random.default_rng(1)

    client.create_collection(
        collection_name="count_test",
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    )

    points = []
    for i in range(n):
        points.append(
            PointStruct(
                id=i + 1,
                vector=rng.normal(size=dim).tolist(),
            )
        )

    client.upsert(collection_name="count_test", points=points)
    info = client.get_collection(collection_name="count_test")
    assert info.points_count == n

    client.close()
