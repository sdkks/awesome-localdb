# SurrealDB

> **Category:** multi-model | **License:** BSL-1.1 | **Stars:** ~32,000

## Overview

SurrealDB is a multi-model database that unifies document, graph, vector, and relational paradigms into a single engine with a custom query language (SurrealQL). It runs embedded in Rust and Python with zero external dependencies via the local engine, supports in-memory and persistent storage backends (RocksDB, SurrealKV), and offers full-text search, geospatial queries, and live query subscriptions. The same engine can also run as a distributed server.

## Quick Start

### Rust

```rust
// Cargo.toml: surrealdb = { version = "2", features = ["kv-mem"] }
use serde::{Serialize, Deserialize};
use surrealdb::Surreal;
use surrealdb::engine::local::Mem;

#[derive(Debug, Serialize, Deserialize)]
struct Person {
    name: String,
    age: u8,
}

#[tokio::main]
async fn main() -> surrealdb::Result<()> {
    let db = Surreal::new::<Mem>(()).await?;
    db.use_ns("test").use_db("test").await?;

    // Create a record
    let created: Option<Person> = db
        .create("person")
        .content(Person { name: "Alice".into(), age: 30 })
        .await?;
    println!("Created: {:?}", created);

    // Query with SurrealQL
    let mut result = db
        .query("SELECT * FROM person WHERE age > 25")
        .await?;
    let people: Vec<Person> = result.take(0)?;
    println!("Found: {:?}", people);

    Ok(())
}
```

### Python

```python
# Install: pip install surrealdb>=2.0
from surrealdb import Surreal

# In-memory embedded database
with Surreal("memory://") as db:
    db.use("test", "test")

    # Create a record
    person = db.create("person", {"name": "Alice", "age": 30})
    print("Created:", person)

    # Query with SurrealQL
    result = db.query("SELECT * FROM person WHERE age > 25")
    print("Found:", result)
```

## On-Disk Format

Multi-file (RocksDB LSM-Tree or SurrealKV SSTables) or in-memory. Embedded engines include Mem (in-memory), RocksDB (file-based), and SurrealKV (file-based).

## Core Strengths

- Multi-model engine unifying document, graph, and vector in one system
- Zero-dependency embedded mode via `surrealdb::engine::local` in Rust
- Custom SurrealQL language with graph traversal, subqueries, and live queries
- Built-in vector similarity search and full-text search indexing
- Same engine runs embedded, single-node server, or distributed cluster
- WASM and edge-compatible with cloud sync capability

## Best Use Cases

1. **Local-first applications needing document, graph, and vector in one DB** — No need to integrate separate databases for different data models
2. **AI/ML apps combining vector search with graph relationship traversal** — Run RAG with semantic search and relationship-based filtering in a single query
3. **Desktop and edge apps requiring embedded multi-model storage** — Ship a single binary with full database capabilities
4. **Real-time collaborative apps using live query subscriptions** — Get push-notifications when data changes without polling
5. **Prototyping cloud-native apps locally before scaling to distributed deploy** — Develop locally with embedded mode, deploy to SurrealDB Cloud

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| Rust | [`recipe_document_crud.rs`](rust/src/bin/recipe_document_crud.rs) | Embedded database with document CRUD, SurrealQL queries, and record links |
| Rust | [`recipe_graph_traversal.rs`](rust/src/bin/recipe_graph_traversal.rs) | Graph relationship queries with record links and graph traversal operators |
| Python | [`recipe_document_crud.py`](python/src/recipe_document_crud.py) | Document CRUD with embedded engine, SurrealQL queries, and record linking |
| Python | [`recipe_graph_vector.py`](python/src/recipe_graph_vector.py) | Graph traversals and vector similarity search with combined queries |

## Limitations & Caveats

- License changed to BSL-1.1 in v3.x — not open-source for Database Service use until 2030
- SurrealQL is a custom query language, not standard SQL — requires learning new syntax
- The RocksDB storage backend depends on non-Rust system libraries (rockdb)
- Python embedded mode bundles Rust engine via FFI; first import may be slow
- Some advanced features (live queries, change feeds) require the server binary, not embedded mode

## Further Reading

- [Official Documentation](https://surrealdb.com/docs)
- [Source Repository](https://github.com/surrealdb/surrealdb)
- [SurrealDB Benchmarks](https://surrealdb.com/benchmarks)
- [Embedding SurrealDB](https://surrealdb.com/blog/the-power-of-surrealdb-embedded)
