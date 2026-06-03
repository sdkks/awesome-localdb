# libSQL

> **Category:** relational, vector | **License:** MIT | **Stars:** ~14,000

## Overview

libSQL is an open-source fork of SQLite by the Turso team that adds modern features while maintaining full SQLite compatibility. It supports native vector search for AI embeddings, async I/O for non-blocking queries, WASM compilation for browser and edge, and embedded replicas that keep a local copy synced with a remote database. Use it when you want SQLite's simplicity plus vector search, replication, or WebAssembly support.

## Quick Start

### Python

```python
# Install: pip install libsql-experimental
import libsql_experimental as libsql

# Connect to a local database file
db = libsql.connect("app.db")

# Write
db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)")
db.execute("INSERT INTO users (name) VALUES (?)", ("Alice",))

# Read
results = db.execute("SELECT * FROM users").fetchall()
print(results)
```

### Rust

```rust
// Cargo.toml: libsql = "0.6"
use libsql::Builder;

#[tokio::main]
async fn main() {
    let db = Builder::new_local("app.db").build().await.unwrap();
    let conn = db.connect().unwrap();

    conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)", ()).await.unwrap();
    conn.execute("INSERT INTO users (name) VALUES ('Alice')", ()).await.unwrap();

    let mut rows = conn.query("SELECT * FROM users", ()).await.unwrap();
    while let Some(row) = rows.next().await.unwrap() {
        println!("id={} name={}", row.get::<i64>(0).unwrap(), row.get::<String>(1).unwrap());
    }
}
```

## On-Disk Format

B-Tree Pages -- SQLite-compatible (Single File)

## Core Strengths

- Full SQLite file format and SQL dialect compatibility
- Native vector search for AI embeddings and RAG pipelines
- Async I/O for non-blocking queries in modern runtimes
- WASM support for browser, edge, and serverless environments
- Embedded replicas with remote sync for offline-first apps
- SQLite extension compatibility (FTS5, JSON, Geo)

## Best Use Cases

1. **AI/ML applications needing local vector similarity search** -- Store and query embeddings locally without a separate vector database
2. **Offline-first apps that sync with a cloud database** -- Use embedded replicas to keep a local copy and sync changes
3. **Browser and edge computing with WASM-compiled SQL** -- Run libSQL directly in the browser via WebAssembly
4. **Mobile and desktop apps that embed a SQL database** -- Drop-in SQLite replacement with added features
5. **Serverless functions requiring fast local SQL access** -- Zero-configuration embedded database with SQL interface

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| Python | [`recipe_sql_queries.py`](python/src/recipe_sql_queries.py) | CRUD operations with explicit transactions and WAL mode |
| Python | [`recipe_vector_search.py`](python/src/recipe_vector_search.py) | Store vector embeddings and compute cosine similarity |
| Rust | [`recipe_sql_queries.rs`](rust/src/bin/recipe_sql_queries.rs) | Async CRUD operations with transactions and error handling |

## Limitations & Caveats

- The Python `libsql-experimental` package supports Linux and macOS only (no Windows)
- Vector search requires loading the `libsql-vector` extension at runtime
- WASM support is a separate build target with a reduced feature set
- Embedded replicas need a remote libSQL server (sqld) for sync

## Further Reading

- [Official Documentation](https://docs.turso.tech)
- [Source Repository](https://github.com/tursodatabase/libsql)
- [libSQL vs SQLite](https://turso.tech/blog/libsql-vs-sqlite)
- [Introducing libSQL](https://turso.tech/blog/introducing-libsql)
