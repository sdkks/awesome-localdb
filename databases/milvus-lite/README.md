# Milvus Lite

> **Category:** Vector | **License:** Apache-2.0 | **Stars:** ~32k

## Overview

Milvus Lite is the lightweight embedded version of Milvus, the open-source, high-performance vector database. Packaged inside pymilvus, it runs entirely in-process with no external dependencies — just `pip install pymilvus` and pass a local `.db` path to `MilvusClient`. It exposes the full pymilvus API surface (collection CRUD, vector insertion, ANN search with scalar filtering, metadata queries) so code written for Milvus Lite migrates seamlessly to Milvus Standalone, Milvus Distributed, or Zilliz Cloud.

## Quick Start

### Python

```python
# Install: pip install pymilvus
from pymilvus import MilvusClient
import numpy as np

# Connect / open (local .db file starts Milvus Lite automatically)
client = MilvusClient("./milvus_demo.db")

# Create a collection with a vector field
client.create_collection(
    collection_name="docs",
    dimension=128,
)

# Insert documents with vectors and metadata
data = [
    {"id": i, "vector": np.random.randn(128).tolist(), "text": f"Doc {i}", "topic": f"topic_{i % 5}"}
    for i in range(100)
]
client.insert("docs", data)

# Vector search with metadata filter
query_vector = np.random.randn(128).tolist()
results = client.search(
    collection_name="docs",
    data=[query_vector],
    limit=5,
    filter="topic in ['topic_1', 'topic_2']",
    output_fields=["text", "topic"],
)
print(results)
```

## On-Disk Format

LSM-style with WAL, immutable Parquet segments, and segment-level FAISS indexes (multi-file per data_dir)

## Core Strengths

- Zero-configuration embedded mode via a local `.db` path
- Full pymilvus API compatibility for seamless migration to production Milvus
- Segment-level FAISS indexes for fast approximate nearest neighbor search
- Scalar filtering combined with vector search in a single query
- BM25 full-text search alongside dense and sparse vector search
- Optional gRPC server mode for multi-client local development

## Best Use Cases

1. **RAG Prototyping** -- Build retrieval-augmented generation pipelines locally with the same API you would use in production.
2. **Notebook Experimentation** -- Explore vector search in Jupyter notebooks with zero infrastructure.
3. **Testing** -- Write unit and integration tests for pymilvus-based applications without deploying Milvus.

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| Python | [`recipe_vector_search.py`](python/src/recipe_vector_search.py) | Create collection, insert vectors, ANN search with scalar filtering |
| Python | [`recipe_collections.py`](python/src/recipe_collections.py) | Create, list, inspect, and drop collections |

## Limitations & Caveats

- A single `data_dir` can only be used by one process at a time (file-locked).
- Designed for local development and small-scale workloads, not distributed production serving.
- No authentication, RBAC, or multi-tenancy support.
- The Milvus Lite CLI server (`milvus-lite server`) requires installing the separate `milvus-lite` package.

## Further Reading

- [Milvus Lite Documentation](https://milvus.io/docs/milvus_lite.md)
- [Source Repository (milvus-io/milvus)](https://github.com/milvus-io/milvus)
- [Milvus Lite Standalone Repo](https://github.com/milvus-io/milvus-lite)
- [PyMilvus API Reference](https://milvus.io/api-reference/pymilvus/v2.5.x/About.md)
