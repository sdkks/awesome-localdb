"""
Recipe: Vector Search with Scalar Filtering
Database: Milvus Lite
Description: Demonstrates creating a collection, inserting documents with vectors and
             metadata, performing ANN vector search, and filtering by scalar fields.

Usage: python src/recipe_vector_search.py
"""

import numpy as np
from pymilvus import MilvusClient


def main() -> None:
    # 1. Setup -- connect to a local .db file (starts Milvus Lite automatically)
    client = MilvusClient("./milvus_recipe.db")

    # 2. Write -- create a collection with a vector field and insert data
    dim = 128
    rng = np.random.default_rng(42)

    client.create_collection(
        collection_name="articles",
        dimension=dim,
    )

    num_docs = 100
    data = [
        {
            "id": i,
            "vector": rng.normal(size=dim).tolist(),
            "title": f"Document number {i} about topic {i % 5}",
            "topic": f"topic_{i % 5}",
            "score": int(rng.integers(0, 100)),
        }
        for i in range(num_docs)
    ]
    client.insert("articles", data)

    stats = client.get_collection_stats("articles")
    print(f"Inserted {stats['row_count']} documents into collection 'articles'")

    # 3. Read -- query by embedding vector (ANN search)
    query_vector = rng.normal(size=dim).tolist()

    # Basic vector search (no scalar filter)
    results = client.search(
        collection_name="articles",
        data=[query_vector],
        limit=5,
        output_fields=["title", "topic"],
    )
    print("\nTop 5 vector search results (no filter):")
    for i, hit in enumerate(results[0]):
        title = hit["entity"].get("title", "N/A")
        distance = hit["distance"]
        print(f"  {i+1}. id={hit['id']} distance={distance:.4f} title='{title}'")

    # Vector search with scalar filter (only topic_3)
    filtered = client.search(
        collection_name="articles",
        data=[query_vector],
        limit=5,
        filter="topic == 'topic_3'",
        output_fields=["title", "topic", "score"],
    )
    print("\nTop 5 results filtered to topic='topic_3':")
    for i, hit in enumerate(filtered[0]):
        entity = hit["entity"]
        title = entity.get("title", "N/A")
        score = entity.get("score", "N/A")
        distance = hit["distance"]
        print(f"  {i+1}. id={hit['id']} distance={distance:.4f} score={score} title='{title}'")

    # Scalar-only query (no vector, pure metadata filter)
    rows = client.query(
        collection_name="articles",
        filter="topic == 'topic_4' and score > 80",
        output_fields=["title", "score", "topic"],
        limit=5,
    )
    print(f"\nScalar query results (topic_4, score > 80) — {len(rows)} rows:")
    for row in rows:
        print(f"  id={row['id']} score={row['score']} title='{row['title']}'")

    # 4. Cleanup
    client.drop_collection("articles")
    print("\nDone. Collection 'articles' dropped.")


if __name__ == "__main__":
    main()
