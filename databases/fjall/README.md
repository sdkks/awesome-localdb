# fjall

> **Category:** Key-Value | **License:** Apache-2.0 | **Stars:** ~2,100

## Overview

Fjall is a log-structured, embeddable key-value storage engine written in 100% safe Rust. It uses an LSM-tree-based storage model similar to RocksDB, providing a thread-safe BTreeMap-like API. Fjall supports multiple keyspaces (analogous to column families) with cross-keyspace atomic semantics, range and prefix searching with forward and reverse iteration, optional serializable transactions, built-in compression (LZ4 by default), and automatic background maintenance. It is designed as an embeddable library -- not a standalone server -- and has no notion of columns or query language.

## Quick Start

### Rust

```rust
// Cargo.toml: fjall = "3"
use fjall::{Database, KeyspaceCreateOptions, PersistMode};

fn main() -> fjall::Result<()> {
    let db = Database::builder("mydb").open()?;

    // Each keyspace is its own isolated LSM-tree
    let items = db.keyspace("my_items", KeyspaceCreateOptions::default())?;

    // Write
    items.insert("greeting", b"Hello from fjall")?;

    // Read
    if let Some(bytes) = items.get("greeting")? {
        println!("greeting = {}", String::from_utf8_lossy(&bytes));
    }

    // Remove
    items.remove("greeting")?;

    // Ensure durability
    db.persist(PersistMode::SyncAll)?;

    Ok(())
}
```

## On-Disk Format

LSM-Tree (SST files + WAL journal)

## Core Strengths

- 100% safe Rust with no unsafe blocks, easy to audit and trust
- LSM-tree storage with automatic background compaction and maintenance
- Multiple keyspaces (column families) with cross-keyspace atomic semantics
- Thread-safe BTreeMap-like API with range and prefix iteration
- Built-in LZ4 compression with configurable compression levels
- Optional serializable transactions via optimistic or single-writer concurrency

## Best Use Cases

1. **Embedded LSM Key-Value** -- Use fjall as a fast, durable embedded store in Rust apps that need LSM-tree write characteristics.
2. **CLI Tool State** -- Persist configuration, caches, and incremental state in single-binary Rust CLI tools.
3. **Edge and IoT** -- Pure safe Rust with no C dependencies makes fjall trivial to cross-compile for ARM, RISC-V, and other targets.
4. **Ordered Key Iteration** -- Range and prefix scans with forward and reverse iteration for ordered data access patterns.
5. **Multi-Keyspace Workloads** -- Isolate data domains into separate keyspaces with cross-keyspace atomicity.

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| Rust | [`recipe_kv_store.rs`](rust/src/bin/recipe_kv_store.rs) | Basic open, insert, get, delete, prefix scan, and range iteration |
| Rust | [`recipe_keyspaces.rs`](rust/src/bin/recipe_keyspaces.rs) | Multiple keyspaces with cross-keyspace operations and transactions |

## Limitations & Caveats

- Embedded-only: no network server, replication protocol, or clustering support.
- Keys are limited to 65536 bytes and values to 2^32 bytes.
- LSM-tree read amplification: point lookups on large datasets may be slower than B-tree-based alternatives without proper tuning.
- Performance is sensitive to compaction strategy configuration -- tune for your workload.
- The database format may change across major versions; breaking changes will include a migration path.
- Key-value separation (large blob support) is an opt-in feature that requires separate configuration.

## Further Reading

- [Official Documentation](https://docs.rs/fjall)
- [Source Repository](https://github.com/fjall-rs/fjall)
- [Project Homepage](https://fjall-rs.github.io)
- [Fjall 3.0 Release Post](https://fjall-rs.github.io/post/fjall-3/)
- [LSM-tree Crate (underlying storage)](https://crates.io/crates/lsm-tree)
