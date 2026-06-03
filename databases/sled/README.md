# Sled

> **Category:** Key-Value | **License:** Apache-2.0 | **Stars:** ~9,000

## Overview

Sled is a high-performance embedded key-value database written in Rust with an API similar to a threadsafe `BTreeMap<[u8], [u8]>`. It uses a lock-free Bw-Tree index and log-structured storage optimized for SSDs, providing fully serializable ACID transactions across multiple keyspaces. Sled supports atomic single-key operations including compare-and-swap and update-and-fetch, zero-copy reads, write batches, subscription/watch semantics on key prefixes, merge operators, and a crash-safe monotonic ID generator capable of 75-125 million IDs per second.

## Maintenance Caveat

The main branch contains an in-progress v1 rewrite with a fundamentally new storage engine and API (version `1.0.0-alpha.124`). The latest published stable release on crates.io is `0.34.7`, which uses the pre-rewrite architecture. The on-disk format is not stable across alpha versions and may change without migration paths. For production use, stick with published crates.io releases (`0.34.x`), and expect the v1 API to differ significantly when it stabilizes.

## Quick Start

### Rust

```rust
// Cargo.toml: sled = "0.34"
use sled;

fn main() -> sled::Result<()> {
    let db = sled::open("my_database")?;

    // Insert and get
    db.insert(b"greeting", b"Hello from sled")?;
    if let Some(val) = db.get(b"greeting")? {
        println!("greeting = {}", String::from_utf8_lossy(&val));
    }

    // Atomic compare-and-swap
    db.compare_and_swap(
        b"greeting",
        Some(b"Hello from sled"), // expected old value
        Some(b"Updated greeting"), // new value
    )?;

    // Range scan
    for kv in db.range(b"key_a"..b"key_z") {
        let (key, val) = kv?;
        println!("{} => {}", String::from_utf8_lossy(&key), String::from_utf8_lossy(&val));
    }

    // Remove and flush
    db.remove(b"greeting")?;
    db.flush()?;

    Ok(())
}
```

## On-Disk Format

Log-structured Bw-Tree (multi-file with pagecache and sequential WAL segments)

## Core Strengths

- Lock-free Bw-Tree and log-structured storage for SSD-optimized concurrent access
- API similar to a threadsafe BTreeMap with serializable ACID transactions
- Fully atomic single-key operations: compare-and-swap, update-and-fetch, merge
- Prefix-encoded and suffix-truncated keys for reduced storage overhead
- Crash-safe monotonic ID generator producing 75-125 million unique IDs per second
- Subscription/watch semantics and reactive iteration over key prefix changes

## Best Use Cases

1. **Embedded Transactional Store** -- Use sled as a lock-free embedded key-value store in Rust applications needing concurrent reads and writes.
2. **Stateful System Component** -- Build larger systems on top of sled's ACID transactions and multiple keyspace isolation.
3. **High-Concurrency Workloads** -- Leverage the lock-free Bw-Tree for workloads where lock contention would bottleneck a traditional B-tree.
4. **SSD-Optimized Persistence** -- Benefit from log-structured writes and low write amplification on flash storage.
5. **CLI Tool State** -- Persist configuration, caches, and incremental state in single-binary Rust CLI tools.

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| Rust | [`recipe_kv_store.rs`](rust/src/bin/recipe_kv_store.rs) | Basic open, insert, get, delete, range scan, compare-and-swap, and flush |

## Limitations & Caveats

- **Active rewrite**: The main branch is undergoing a v1 rewrite. The published 0.34.x API will differ from the eventual v1 API.
- **No stable on-disk format**: Alpha versions (1.0.0-alpha.x) do not guarantee forward or backward compatibility.
- **Embedded-only**: No network server, replication protocol, or clustering support.
- **Optimistic transactions**: Transaction closures must not perform IO or interact with external state (must be idempotent).
- **Durability**: Automatic fsync every 500ms by default; call `flush()` or configure `flush_every_ms` for stronger guarantees.
- **In-memory overhead**: The lock-free Bw-Tree keeps a significant portion of the index in memory for concurrent access.

## Further Reading

- [Official Website](https://sled.rs)
- [API Documentation (docs.rs)](https://docs.rs/sled)
- [Source Repository](https://github.com/spacejam/sled)
- [Architectural Outlook](https://github.com/spacejam/sled/wiki/sled-architectural-outlook)
- [Database of Databases Entry](https://dbdb.io/db/sled)
