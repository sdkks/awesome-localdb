# Limbo

> **Category:** Relational | **License:** Apache-2.0 | **Stars:** ~19,000 | **Status:** Beta

## Overview

Limbo is an in-progress complete rewrite of SQLite in Rust by the Turso team. It targets full compatibility with SQLite's SQL dialect and file format while adding ground-up support for fully asynchronous I/O (io_uring on Linux) and a WASM-first build target for browser and edge environments. Limbo integrates Deterministic Simulation Testing (DST) into its core and is intended to eventually become the next evolution of libSQL.

**Important:** Limbo is in **beta** and not yet production-ready. The API and on-disk format may change without backward compatibility guarantees.

## Quick Start

### Rust

```rust
// Cargo.toml: limbo = "0.0"
use limbo::{Builder, Value};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Open (or create) a local database — fully async I/O
    let db = Builder::new_local("app.db").build().await?;
    let conn = db.connect()?;

    // Schema
    conn.execute(
        "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)",
        (),
    ).await?;

    // Write — async execute
    conn.execute(
        "INSERT INTO users (name, email) VALUES (?1, ?2)",
        limbo::params!["Alice", "alice@example.com"],
    ).await?;
    conn.execute(
        "INSERT INTO users (name, email) VALUES (?1, ?2)",
        limbo::params!["Bob", "bob@example.com"],
    ).await?;

    // Read — async query with row iteration
    let mut rows = conn.query(
        "SELECT id, name, email FROM users ORDER BY id",
        (),
    ).await?;

    while let Some(row) = rows.next().await? {
        let id = row.get_value(0)?;
        let name = row.get_value(1)?;
        let email = row.get_value(2)?;
        if let (Value::Integer(id), Value::Text(name), Value::Text(email)) = (id, name, email) {
            println!("[{}] {} <{}>", id, name, email);
        }
    }

    // Cleanup
    drop(conn);
    drop(db);
    std::fs::remove_file("app.db")?;

    Ok(())
}
```

> **Note:** Limbo is in beta (v0.0.x). The crate name is `limbo` on crates.io. API surface and feature set are evolving rapidly.

## On-Disk Format

SQLite-compatible B-Tree Pages (Single File)

## Core Strengths

- Memory-safe SQLite rewrite in Rust with full SQL dialect and file format compatibility
- Fully asynchronous I/O from the ground up with io_uring support on Linux
- WASM-first design for native browser, edge, and serverless environments
- Deterministic Simulation Testing (DST) integrated into the core for reliability
- Performance on par or faster than SQLite for common query operations
- Open-contribution development model under the Turso umbrella

## Best Use Cases

1. **Rust applications needing a memory-safe embedded SQL database** -- Use Limbo where you want SQLite compatibility without C dependencies.
2. **Browser and edge computing with WASM-compiled SQL** -- Limbo's WASM-first design targets environments where SQLite's WASM support is an afterthought.
3. **Applications requiring fully asynchronous SQL operations** -- No helper threads needed; Limbo's async I/O is built into the core.
4. **Desktop and mobile apps needing a SQLite-compatible embedded database in Rust** -- Pure Rust implementation, easy to cross-compile.
5. **Developers who want SQLite compatibility with modern async and WASM features** -- Familiar SQL interface with modern architectural choices.

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| Rust | [`recipe_sql_queries.rs`](rust/src/bin/recipe_sql_queries.rs) | Async CRUD operations: create table, insert, select, update, delete |

## Limitations & Caveats

- **Beta status:** Not production-ready. API, on-disk format, and feature set may change without notice.
- **Incomplete SQLite compatibility:** Not all SQLite features are implemented. Check the project's compatibility tracking for current coverage.
- **WASM support in development:** Browser support is actively being built but not yet complete.
- **Repository scope:** The GitHub repo (tursodatabase/turso) contains the full Turso database project; Limbo is a component within it.
- **No built-in replication or server:** Limbo is embedded-only with no network server, replication, or clustering.

## Further Reading

- [Introducing Limbo (Turso Blog)](https://turso.tech/blog/introducing-limbo-a-complete-rewrite-of-sqlite-in-rust)
- [Source Repository](https://github.com/tursodatabase/turso)
- [Limbo crate on crates.io](https://crates.io/crates/limbo)
- [Limbo API documentation on docs.rs](https://docs.rs/limbo)
