"""
Recipe: Vector Search with Metadata Filtering
Database: ChromaDB
Description: Demonstrates creating a collection, adding documents with embeddings and
             metadata, performing vector similarity search, and filtering by metadata.

Usage: python src/recipe_vector_search.py
"""

import chromadb
import numpy as np


def main() -> None:
    # 1. Setup -- create an ephemeral in-memory client
    client = chromadb.Client()

    # 2. Write -- create a collection and add documents with embeddings
    dim = 128
    rng = np.random.default_rng(42)

    collection = client.create_collection(name="articles")

    # Generate synthetic embeddings and documents
    num_docs = 100
    embeddings = rng.normal(size=(num_docs, dim)).tolist()
    documents = [f"Document number {i} about topic {i % 5}" for i in range(num_docs)]
    ids = [f"doc_{i}" for i in range(num_docs)]
    metadatas = [
        {"topic": str(i % 5), "score": float(rng.integers(0, 100))}
        for i in range(num_docs)
    ]

    collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
    print(f"Added {collection.count()} documents to collection 'articles'")

    # 3. Read -- query by embedding vector
    query_embedding = rng.normal(size=dim).tolist()

    # Basic vector search (pure similarity, no filter)
    results = collection.query(query_embeddings=[query_embedding], n_results=5)
    print("\nTop 5 vector search results (no filter):")
    for i, (doc_id, doc, distance) in enumerate(
        zip(results["ids"][0], results["documents"][0], results["distances"][0])
    ):
        print(f"  {i+1}. id={doc_id} distance={distance:.4f} doc='{doc}'")

    # Vector search with metadata filter (only topic "3")
    filtered = collection.query(
        query_embeddings=[query_embedding],
        n_results=5,
        where={"topic": "3"},
    )
    print("\nTop 5 results filtered to topic='3':")
    for i, (doc_id, doc, distance) in enumerate(
        zip(filtered["ids"][0], filtered["documents"][0], filtered["distances"][0])
    ):
        print(f"  {i+1}. id={doc_id} distance={distance:.4f} doc='{doc}'")

    # 4. Cleanup -- ephemeral client requires no explicit cleanup
    print("\nDone. Ephemeral client data is discarded on exit.")


if __name__ == "__main__":
    main()
