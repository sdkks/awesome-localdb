# LanceDB

> **Category:** Vector | **License:** Apache-2.0 | **Stars:** ~10.5k

## Overview

LanceDB is a developer-friendly, open-source embedded vector database purpose-built for multimodal AI workloads. It uses the Lance columnar format (Arrow-native) to store raw data, embeddings, and metadata together, enabling zero-copy reads and fast vector search. With no server required, LanceDB runs directly in-process, making it ideal for local development and edge deployments while still scaling to cloud object storage.

## Quick Start

### Python

```python
# Install: pip install lancedb
import lancedb
import numpy as np

# Connect / open
db = lancedb.connect("mydb.lance")

# Create a table with embeddings
data = [
    {"id": 1, "vector": np.random.randn(128).tolist(), "text": "hello world"},
    {"id": 2, "vector": np.random.randn(128).tolist(), "text": "goodbye moon"},
]
table = db.create_table("docs", data=data)

# Vector search
query = np.random.randn(128).tolist()
results = table.search(query).limit(5).to_pandas()
print(results)
```

### TypeScript

```typescript
// Install: npm install @lancedb/lancedb
import * as lancedb from "@lancedb/lancedb";

const db = await lancedb.connect("mydb.lance");
const table = await db.createTable("docs", [
  { id: 1, vector: Array.from({length: 128}, () => Math.random()), text: "hello" },
]);
const results = await table.search(Array.from({length: 128}, () => Math.random())).limit(5).toArray();
```

### Rust

```rust
// Cargo.toml: lancedb = "0.17"
use lancedb::{connect};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let db = connect("mydb.lance").execute().await?;
    // ...
    Ok(())
}
```

## On-Disk Format

Lance Columnar Format (Arrow-native, multi-file)

## Core Strengths

- Arrow-native vector search with zero-copy reads
- Multimodal data -- text, images, embeddings in one table
- Embedded-first with no server required
- Separation of storage and compute for cloud scale
- Fast approximate nearest neighbor search (IVF-PQ, HNSW)
- SQL-like filtering with metadata alongside vectors

## Best Use Cases

1. **RAG Pipelines** -- Store document chunks and embeddings for retrieval-augmented generation with LLMs.
2. **Multimodal AI** -- Combine text, image, and vector data in a single table for cross-modal search.
3. **Local-First Vector Search** -- Embed directly into desktop, mobile, and edge applications with no external service dependency.

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| Python | [`recipe_vector_search.py`](python/src/recipe_vector_search.py) | Create table, add embeddings, vector search with metadata filtering |
| Python | [`recipe_multimodal_storage.py`](python/src/recipe_multimodal_storage.py) | Store text + embeddings + metadata, hybrid query |

## Limitations & Caveats

- LanceDB v1 uses a multi-file on-disk format; use v0.x for true single-file portability.
- Vector index creation is a separate explicit step; queries without an index perform brute-force search.
- Cloud object storage support (S3/GCS/Azure) requires additional configuration.

## Further Reading

- [Official Documentation](https://lancedb.github.io/lancedb/)
- [Source Repository](https://github.com/lancedb/lancedb)
