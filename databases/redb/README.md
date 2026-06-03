# redb

> **Category:** Key-Value | **License:** Apache-2.0 OR MIT | **Stars:** ~3,500

## Overview

redb is a simple, portable, high-performance, ACID-compliant embedded key-value store written in pure Rust. It uses a collection of copy-on-write B-trees, providing MVCC support that allows a writer and concurrent readers to operate without blocking each other. The entire database is stored in a single file, making it easy to manage and deploy. redb is loosely inspired by LMDB but is implemented entirely in Rust with no C dependencies, and exposes a type-safe API via `TableDefinition` and `MultimapTableDefinition`.

## Quick Start

### Rust

```rust
// Cargo.toml: redb = "4"
use redb::{Database, ReadableDatabase, ReadableTable, TableDefinition};

const TABLE: TableDefinition<&str, &str> = TableDefinition::new("kv");

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let db = Database::create("mydb.redb")?;

    // Write
    let write_txn = db.begin_write()?;
    {
        let mut table = write_txn.open_table(TABLE)?;
        table.insert("greeting", "Hello from redb")?;
    }
    write_txn.commit()?;

    // Read
    let read_txn = db.begin_read()?;
    let table = read_txn.open_table(TABLE)?;
    if let Some(entry) = table.get("greeting")? {
        println!("greeting = {}", entry.value());
    }

    Ok(())
}
```

## On-Disk Format

Copy-on-Write B-Tree (single file)

## Core Strengths

- Pure Rust implementation with zero C dependencies, easy to cross-compile
- MVCC with concurrent readers and writer via copy-on-write B-trees
- Fully ACID-compliant transactions with crash safety by default
- Type-safe typed table API supporting arbitrary Rust key and value types
- Single-file storage format, simple to deploy and back up
- Savepoints and rollbacks for fine-grained transaction control

## Best Use Cases

1. **Rust Desktop Applications** -- Embed a durable, ACID-compliant store directly in Tauri, egui, or Iced apps without external processes.
2. **CLI Tool State** -- Persist configuration, caches, and incremental state in single-binary Rust CLI tools.
3. **Local Caching Layers** -- Fast, consistent key-value lookups in Rust microservices and daemons.
4. **Edge and IoT** -- Pure Rust compilation makes redb trivial to cross-compile for ARM, RISC-V, and WASM targets.
5. **LMDB Replacement** -- Familiar MVCC + B-tree model in a pure-Rust crate with no unsafe system dependencies.

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| Rust | [`recipe_kv_store.rs`](rust/src/bin/recipe_kv_store.rs) | Basic open, insert, get, delete, and cursor iteration |
| Rust | [`recipe_typed_tables.rs`](rust/src/bin/recipe_typed_tables.rs) | Typed tables with multiple data types and range queries |

## Limitations & Caveats

- Single-writer by design: only one write transaction at a time. Writes are serialized.
- The database file grows monotonically. Call `Database::compact()` periodically to reclaim space from deleted data.
- A long-running read transaction will prevent compaction from freeing space.
- Maximum key size is limited by the B-tree page size (default 4 KB).
- Embedded-only: no built-in network server, replication, or clustering protocol.
- While redb is WASM-compatible in theory, the default storage backend uses `std::fs` and may not work in all WASI environments. Use an in-memory backend for WASM.

## Further Reading

- [Official Documentation](https://www.redb.org)
- [Source Repository](https://github.com/cberner/redb)
- [Design Document](https://github.com/cberner/redb/blob/master/docs/design.md)
- [Benchmarks](https://github.com/cberner/redb#benchmarks)
