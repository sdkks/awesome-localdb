"""Tests for recipe_vector_search.py"""

import numpy as np

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

from src.recipe_vector_search import main


def test_recipe_runs_without_error():
    """The recipe should execute without raising an exception."""
    main()


def test_create_collection_and_search():
    """Verify collection creation, point count, and vector search return expected results."""
    client = QdrantClient(location=":memory:")

    dim = 64
    rng = np.random.default_rng(13)
    num_points = 20

    client.create_collection(
        collection_name="test_docs",
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    )

    points = []
    for i in range(num_points):
        points.append(
            PointStruct(
                id=i + 1,
                vector=rng.normal(size=dim).tolist(),
                payload={"kind": "a" if i < 10 else "b"},
            )
        )

    client.upsert(collection_name="test_docs", points=points)
    info = client.get_collection(collection_name="test_docs")
    assert info.points_count == num_points

    query_vector = rng.normal(size=dim).tolist()
    results = client.query_points(
        collection_name="test_docs",
        query=query_vector,
        limit=3,
    )
    assert len(results.points) == 3
    for hit in results.points:
        assert hit.id is not None
        assert hit.score is not None
        assert hit.payload is not None

    client.close()


def test_vector_search_with_payload_filter():
    """Vector search with payload filter should return only matching rows."""
    client = QdrantClient(location=":memory:")

    dim = 32
    rng = np.random.default_rng(42)
    num_points = 20

    client.create_collection(
        collection_name="test_filter",
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    )

    points = []
    for i in range(num_points):
        color = "red" if i < 10 else "blue"
        points.append(
            PointStruct(
                id=i + 1,
                vector=rng.normal(size=dim).tolist(),
                payload={"color": color},
            )
        )

    client.upsert(collection_name="test_filter", points=points)

    query_vector = rng.normal(size=dim).tolist()
    results = client.query_points(
        collection_name="test_filter",
        query=query_vector,
        query_filter=Filter(
            must=[FieldCondition(key="color", match=MatchValue(value="red"))],
        ),
        limit=10,
    )
    assert len(results.points) <= 10
    # All returned payloads should have color "red"
    for hit in results.points:
        assert hit.payload["color"] == "red"

    client.close()
