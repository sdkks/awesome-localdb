"""
Recipe: Collection Management
Database: Qdrant Local Mode
Description: Demonstrates creating, listing, inspecting, and deleting collections
             using Qdrant's collection-based organization model.

Usage: python src/recipe_collections.py
"""

import tempfile
import os

import numpy as np

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct


def main() -> None:
    # 1. Setup -- use in-memory mode for ephemeral collections
    client = QdrantClient(location=":memory:")

    # 2. Create collections
    client.create_collection(
        collection_name="users",
        vectors_config=VectorParams(size=64, distance=Distance.COSINE),
    )
    client.create_collection(
        collection_name="products",
        vectors_config=VectorParams(size=64, distance=Distance.COSINE),
    )
    client.create_collection(
        collection_name="orders",
        vectors_config=VectorParams(size=64, distance=Distance.COSINE),
    )
    print("Created 3 collections: users, products, orders")

    # 3. List all collections
    collections = client.get_collections()
    print(f"\nAll collections ({len(collections.collections)}):")
    for col in collections.collections:
        print(f"  - {col.name}")

    # 4. Collection exists check (idempotent)
    exists = client.collection_exists(collection_name="products")
    print(f"\ncollection_exists('products') -> {exists}")

    exists_new = client.collection_exists(collection_name="analytics")
    print(f"collection_exists('analytics') -> {exists_new}")
    if not exists_new:
        client.create_collection(
            collection_name="analytics",
            vectors_config=VectorParams(size=64, distance=Distance.COSINE),
        )
        print("  Created new collection 'analytics'")

    # 5. Add data and inspect count
    rng = np.random.default_rng(7)
    dim = 64
    points = []
    for i in range(10):
        points.append(
            PointStruct(
                id=i + 1,
                vector=rng.normal(size=dim).tolist(),
                payload={"name": f"User profile {i}"},
            )
        )
    client.upsert(collection_name="users", points=points)
    info = client.get_collection(collection_name="users")
    print(f"\nAdded 10 users to 'users' collection (points: {info.points_count})")

    # 6. Delete a collection
    client.delete_collection(collection_name="orders")
    remaining = client.get_collections()
    print(f"Deleted 'orders' collection. Remaining ({len(remaining.collections)}):")
    for col in remaining.collections:
        cinfo = client.get_collection(collection_name=col.name)
        print(f"  - {col.name} (points: {cinfo.points_count})")

    # 7. Cleanup
    client.close()
    print("\nDone. In-memory data is discarded on exit.")


if __name__ == "__main__":
    main()
