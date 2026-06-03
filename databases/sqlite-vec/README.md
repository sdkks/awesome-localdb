# sqlite-vec

> **Category:** Vector | **License:** MIT | **Stars:** ~7.7k

## Overview

sqlite-vec is an extremely small, "fast enough" vector search SQLite extension that runs everywhere SQLite runs -- desktop, mobile, edge devices, and browsers via WASM. Created by Alex Garcia, it stores vectors as compact BLOBs in regular SQLite tables and exposes vector operations through standard SQL functions and virtual tables. With no external dependencies and a simple `pip install sqlite-vec`, it brings vector search to any application that already uses SQLite.

## Quick Start

### Python

```python
# Install: pip install sqlite-vec
import sqlite3
import sqlite_vec
from sqlite_vec import serialize_float32

# Connect and load the extension
db = sqlite3.connect(":memory:")
db.enable_load_extension(True)
sqlite_vec.load(db)
db.enable_load_extension(False)

# Create a virtual table for 4-dimensional float vectors
db.execute("CREATE VIRTUAL TABLE items USING vec0(embedding float[4])")

# Insert vectors with metadata
vectors = [
    [0.1, 0.2, 0.3, 0.4],
    [0.5, 0.6, 0.7, 0.8],
    [0.9, 0.1, 0.2, 0.3],
]
for v in vectors:
    db.execute(
        "INSERT INTO items VALUES (?)",
        [serialize_float32(v)],
    )

# Exact KNN search
query = serialize_float32([0.15, 0.25, 0.35, 0.45])
results = db.execute(
    "SELECT rowid, distance FROM items WHERE embedding MATCH ? ORDER BY distance LIMIT 2",
    [query],
).fetchall()
print(results)
```

### Node.js

```javascript
// Install: npm install sqlite-vec
import Database from "better-sqlite3";
import * as sqlite_vec from "sqlite-vec";

const db = new Database(":memory:");
sqlite_vec.load(db);

db.exec("CREATE VIRTUAL TABLE items USING vec0(embedding float[4])");

const { sqlite3_api } = sqlite_vec;
// Insert and search vectors with standard SQL
```

## On-Disk Format

SQLite extension (vectors stored as BLOBs in standard SQLite tables + virtual tables)

## Core Strengths

- Runs anywhere SQLite runs -- desktop, mobile, edge, WASM
- Extremely small footprint with zero external dependencies
- Full SQL interface for vector operations (insert, search, filter)
- Supports float32, int8, binary, and sparse vector types
- Exact KNN search with SQL ORDER BY distance LIMIT k
- Hybrid search combining vector similarity with structured WHERE filters

## Best Use Cases

1. **RAG Pipelines** -- Store document chunk embeddings in SQLite and retrieve relevant context for LLMs.
2. **On-Device Vector Search** -- Embed vector search into mobile apps and edge devices with no server dependency.
3. **Semantic Search for Existing Apps** -- Add vector capabilities to applications already using SQLite without swapping databases.

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| Python | [`recipe_vector_search.py`](python/src/recipe_vector_search.py) | Create table, store embeddings, exact KNN vector search |
| Python | [`recipe_hybrid_search.py`](python/src/recipe_hybrid_search.py) | Vector search combined with metadata filtering |

## Limitations & Caveats

- Currently performs exact (brute-force) KNN search; approximate nearest neighbor (ANN) via DiskANN is in development.
- Requires SQLite 3.41+ for full feature support.
- On macOS, the system Python does not support loadable SQLite extensions; use Homebrew Python or `pysqlite3`.
- Vector index creation and metadata filtering are expressed through standard SQL, not a separate query API.

## Further Reading

- [Official Documentation](https://alexgarcia.xyz/sqlite-vec/)
- [Source Repository](https://github.com/asg017/sqlite-vec)
