# SQLite

> **Category:** Relational | **License:** Public Domain | **Stars:** ~9,700

## Overview

SQLite is a self-contained, serverless, zero-configuration SQL database engine. It reads and writes directly to ordinary disk files — no daemon, no setup, just a library you link into your application. With over a trillion databases in active use, SQLite is the most widely deployed database engine in the world, powering every smartphone, every web browser, and countless desktop and embedded applications.

## Quick Start

### Python

```python
# Built-in — no install needed (sqlite3 is in the Python standard library)
import sqlite3

# Connect to a file (creates it if it doesn't exist)
db = sqlite3.connect("app.db")

# Enable WAL mode for better concurrency
db.execute("PRAGMA journal_mode=WAL")

# Write
db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)")
db.execute("INSERT INTO users (name) VALUES (?)", ("Alice",))
db.commit()

# Read
results = db.execute("SELECT * FROM users").fetchall()
print(results)  # [(1, 'Alice')]

db.close()
```

### Rust

```rust
// Cargo.toml: rusqlite = { version = "0.31", features = ["bundled"] }
use rusqlite::Connection;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let db = Connection::open("app.db")?;

    db.execute_batch("PRAGMA journal_mode=WAL")?;
    db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)", [])?;
    db.execute("INSERT INTO users (name) VALUES (?1)", ["Alice"])?;

    let mut stmt = db.prepare("SELECT * FROM users")?;
    let rows: Vec<String> = stmt
        .query_map([], |row| row.get(1))?
        .filter_map(|r| r.ok())
        .collect();

    println!("{:?}", rows); // ["Alice"]
    Ok(())
}
```

## On-Disk Format

B-Tree Pages (Single File)

## Core Strengths

- ACID compliant — full transactional guarantees even after power loss
- Zero-configuration, serverless — no install, no daemon, no ports
- Universally supported across all platforms and languages
- Battle-tested — spacecraft-grade reliability with over 100% branch test coverage
- Single-file database, easy to copy, backup, and share
- Full SQL support with powerful extensions (FTS5 full-text search, JSON functions, Geo)

## Best Use Cases

1. **Transactional local storage for applications** — The canonical choice for local relational data. Use it anywhere you need structured, queryable storage without a server.
2. **Mobile apps (iOS/Android built-in)** — Both platforms ship SQLite as part of the OS. It is the default local database for both Core Data (iOS) and Room (Android).
3. **Local data for CLI tools and MCP servers** — Perfect for tools that need to persist structured state between invocations without external dependencies.
4. **Offline-first web apps (via OPFS)** — The official SQLite WASM build runs in browsers using the Origin Private File System, enabling full SQL in the browser.
5. **Embedded systems and IoT devices** — SQLite compiles to a few hundred KB, runs on bare metal, and handles the constrained environments of IoT and embedded systems.

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| Python | [`recipe_transactional_storage.py`](python/src/recipe_transactional_storage.py) | CRUD operations with error handling and WAL mode |
| Python | [`recipe_in_memory_cache.py`](python/src/recipe_in_memory_cache.py) | In-memory database as a local cache |
| Rust | [`recipe_transactional_storage.rs`](rust/src/bin/recipe_transactional_storage.rs) | CRUD operations with error handling |
| Rust | [`recipe_in_memory_cache.rs`](rust/src/bin/recipe_in_memory_cache.rs) | In-memory database as a local cache |

## Limitations & Caveats

- SQLite uses a single-writer model by default. Enable WAL mode for concurrent reads during writes.
- Heavy write queues may need additional tuning (auto-vacuum, page size, synchronous pragma).
- Not suited for high-concurrency write workloads — if you need hundreds of concurrent writers, consider a client-server database.
- Limited support for ALTER TABLE compared to PostgreSQL or MySQL (no DROP COLUMN before 3.35.0).

## Further Reading

- [Official Documentation](https://sqlite.org)
- [Source Repository](https://github.com/sqlite/sqlite)
