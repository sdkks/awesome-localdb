# Qdrant Local Mode

> **Category:** Vector | **License:** Apache-2.0 | **Stars:** ~22k

## Overview

Qdrant Local Mode is an embedded, in-process implementation of the Qdrant vector search engine that runs entirely within the Python client. It provides the full Qdrant API surface -- collection CRUD, point management, vector similarity search with payload filtering, and hybrid search -- with no external server required. The same client code transitions seamlessly to Qdrant Server or Qdrant Cloud for production. Local Mode uses brute-force numpy-based search with optional SQLite-backed persistence and is ideal for development, testing, and datasets up to approximately 20,000 points.

## Quick Start

### Python

```python
# Install: pip install qdrant-client
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Connect / open (local mode with path or :memory:)
client = QdrantClient(path="./my_qdrant_data")

# Create a collection
client.create_collection(
    collection_name="articles",
    vectors_config=VectorParams(size=128, distance=Distance.COSINE),
)

# Insert points with vectors and payload
client.upsert(
    collection_name="articles",
    points=[
        PointStruct(id=1, vector=[0.1] * 128, payload={"title": "Hello World"}),
        PointStruct(id=2, vector=[0.2] * 128, payload={"title": "Vector Search"}),
        PointStruct(id=3, vector=[0.3] * 128, payload={"title": "Qdrant Guide"}),
    ],
)

# Search
results = client.search(
    collection_name="articles",
    query_vector=[0.15] * 128,
    limit=3,
)
for hit in results:
    print(f"id={hit.id} score={hit.score:.4f} title={hit.payload['title']}")
```

## On-Disk Format

SQLite-backed persistence (multi-file per storage directory) or ephemeral in-memory

## Core Strengths

- Full Qdrant API surface in-process with zero external dependencies
- Same client code transitions seamlessly to Qdrant Server or Cloud
- Collection-based organization with vector similarity and payload filtering
- Optional SQLite-backed persistence with file-locked exclusive access
- Ephemeral in-memory mode (`:memory:`) for rapid testing and CI/CD
- Supports dense, sparse, and multi-vector search with multiple distance metrics

## Best Use Cases

1. **RAG Pipelines** -- Prototype and develop retrieval-augmented generation workflows locally before deploying to production Qdrant.
2. **Testing and CI/CD** -- Write unit and integration tests against the full Qdrant API without standing up infrastructure.
3. **AI/ML Experimentation** -- Explore vector similarity search, embeddings, and hybrid search in notebooks and scripts.

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| Python | [`recipe_vector_search.py`](python/src/recipe_vector_search.py) | Insert points with vectors and payloads, search by similarity, apply payload filters |
| Python | [`recipe_collections.py`](python/src/recipe_collections.py) | Create, list, inspect, and delete collections |

## Limitations & Caveats

- Designed for datasets up to ~20,000 points per collection; migrate to Qdrant Server or Cloud for larger workloads.
- Uses brute-force search (numpy-based) rather than HNSW indexing; search scales linearly with collection size.
- Only one process may access a persistent storage directory at a time (enforced via `portalocker`).
- Local Mode is included in `qdrant-client` with no separate package required.

## Further Reading

- [Official Documentation](https://qdrant.tech/documentation/)
- [Local Mode Quickstart](https://qdrant.tech/documentation/quickstart/)
- [Source Repository](https://github.com/qdrant/qdrant)
