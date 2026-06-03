"""
Recipe: Collection Management
Database: ChromaDB
Description: Demonstrates creating, listing, inspecting, and deleting collections
             using ChromaDB's collection-based organization model.

Usage: python src/recipe_collection_management.py
"""

import chromadb
import numpy as np


def main() -> None:
    # 1. Setup -- create an ephemeral in-memory client
    client = chromadb.Client()

    # 2. Create collections
    client.create_collection(name="users")
    client.create_collection(name="products")
    client.create_collection(name="orders")
    print("Created 3 collections: users, products, orders")

    # 3. List all collections
    collections = client.list_collections()
    print(f"\nAll collections ({len(collections)}):")
    for col in collections:
        print(f"  - {col.name}")

    # 4. Get or create (idempotent)
    products = client.get_or_create_collection(name="products")
    print(f"\nget_or_create_collection('products') returned existing collection: {products.name}")

    analytics = client.get_or_create_collection(name="analytics")
    print(f"get_or_create_collection('analytics') created new collection: {analytics.name}")

    # 5. Add data and inspect count
    rng = np.random.default_rng(7)
    users_col = client.get_collection(name="users")
    dim = 64
    users_col.add(
        ids=[f"user_{i}" for i in range(10)],
        embeddings=rng.normal(size=(10, dim)).tolist(),
        documents=[f"User profile {i}" for i in range(10)],
    )
    print(f"\nAdded 10 users to 'users' collection (count: {users_col.count()})")

    # 6. Delete a collection
    client.delete_collection(name="orders")
    remaining = client.list_collections()
    print(f"Deleted 'orders' collection. Remaining ({len(remaining)}):")
    for col in remaining:
        print(f"  - {col.name} (count: {col.count()})")

    # 7. Cleanup
    print("\nDone. Ephemeral client data is discarded on exit.")


if __name__ == "__main__":
    main()
