"""
Recipe: Vector Search with Payload Filtering
Database: Qdrant Local Mode
Description: Demonstrates creating a collection, inserting points with vectors and
             payloads, performing vector similarity search, and filtering by payload.

Usage: python src/recipe_vector_search.py
"""

import os
import tempfile

import numpy as np

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue


def main() -> None:
    # 1. Setup -- create a client backed by a temporary directory
    tmpdir = tempfile.mkdtemp(prefix="qdrant_recipe_")
    client = QdrantClient(path=tmpdir)

    try:
        # 2. Write -- create a collection and insert points with vectors and payloads
        dim = 128
        rng = np.random.default_rng(42)

        client.create_collection(
            collection_name="articles",
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )

        num_points = 100
        points = []
        for i in range(num_points):
            vector = rng.normal(size=dim).tolist()
            points.append(
                PointStruct(
                    id=i + 1,
                    vector=vector,
                    payload={
                        "title": f"Document number {i} about topic {i % 5}",
                        "topic": str(i % 5),
                        "score": float(rng.integers(0, 100)),
                    },
                )
            )

        client.upsert(collection_name="articles", points=points)
        info = client.get_collection(collection_name="articles")
        print(f"Inserted {info.points_count} points into collection 'articles'")

        # 3. Read -- search by vector similarity
        query_vector = rng.normal(size=dim).tolist()

        # Basic vector search (no filter)
        results = client.query_points(
            collection_name="articles",
            query=query_vector,
            limit=5,
        )
        print("\nTop 5 vector search results (no filter):")
        for i, hit in enumerate(results.points):
            print(f"  {i+1}. id={hit.id} score={hit.score:.4f} topic={hit.payload['topic']}")

        # Vector search with payload filter (only topic "3")
        filtered = client.query_points(
            collection_name="articles",
            query=query_vector,
            query_filter=Filter(
                must=[FieldCondition(key="topic", match=MatchValue(value="3"))],
            ),
            limit=5,
        )
        print("\nTop 5 results filtered to topic='3':")
        for i, hit in enumerate(filtered.points):
            print(f"  {i+1}. id={hit.id} score={hit.score:.4f} topic={hit.payload['topic']}")

        print("\nDone.")
    finally:
        # 4. Cleanup -- close client and remove temporary data
        client.close()
        for root, dirs, files in os.walk(tmpdir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(tmpdir)


if __name__ == "__main__":
    main()
