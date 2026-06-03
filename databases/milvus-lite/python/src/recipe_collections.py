"""
Recipe: Collection Management
Database: Milvus Lite
Description: Demonstrates creating, listing, inspecting, and dropping collections
             using Milvus Lite's collection-based organization model.

Usage: python src/recipe_collections.py
"""

import numpy as np
from pymilvus import MilvusClient


def main() -> None:
    # 1. Setup -- connect to a local .db file (starts Milvus Lite automatically)
    client = MilvusClient("./milvus_collections.db")

    # 2. Create collections
    client.create_collection(collection_name="users", dimension=64)
    client.create_collection(collection_name="products", dimension=64)
    client.create_collection(collection_name="orders", dimension=64)
    print("Created 3 collections: users, products, orders")

    # 3. List all collections
    collections = client.list_collections()
    print(f"\nAll collections ({len(collections)}):")
    for col_name in collections:
        print(f"  - {col_name}")

    # 4. Describe a collection (schema details)
    desc = client.describe_collection("users")
    print(f"\nCollection 'users' description:")
    for field in desc.get("fields", []):
        print(f"  {field['name']}: type={field['type']}")
    print(f"  auto_id={desc.get('auto_id', False)}")

    # 5. Insert data and check stats
    rng = np.random.default_rng(7)
    user_data = [
        {
            "id": i,
            "vector": rng.normal(size=64).tolist(),
            "name": f"User {i}",
            "active": i % 2 == 0,
        }
        for i in range(10)
    ]
    client.insert("users", user_data)
    stats = client.get_collection_stats("users")
    print(f"\nInserted 10 users into 'users' collection (row_count: {stats['row_count']})")

    # 6. Has collection (check existence)
    print(f"\nHas 'orders'? {client.has_collection('orders')}")
    print(f"Has 'analytics'? {client.has_collection('analytics')}")

    # 7. Drop a collection
    client.drop_collection("orders")
    remaining = client.list_collections()
    print(f"\nDropped 'orders' collection. Remaining ({len(remaining)}):")
    for col_name in remaining:
        row_count = client.get_collection_stats(col_name)["row_count"]
        print(f"  - {col_name} (row_count: {row_count})")

    # 8. Cleanup -- drop remaining collections
    client.drop_collection("users")
    client.drop_collection("products")
    print("\nDone. All collections cleaned up.")


if __name__ == "__main__":
    main()
