# RocksDB

> **Category:** Key-Value | **License:** Apache-2.0 | **Stars:** ~29,900

## Overview

RocksDB is a high-performance embedded key-value store forked from Google's LevelDB and developed by Meta. It is optimized for fast, low-latency storage on flash and persistent memory, using a Log-Structured Merge-Tree (LSM-Tree) design. RocksDB serves as the storage engine for MySQL (MyRocks), Apache Flink, CockroachDB, TiKV, and countless other distributed systems. It offers fine-grained tuning of compaction, compression, bloom filters, and column families for workload-specific performance.

## Quick Start

### Python

```python
# Install: pip install rocksdb-py
import rocksdbpy

# Open
db = rocksdbpy.open_default("mydb.rocksdb")

# Write
db.set(b"hello", b"world")

# Read
value = db.get(b"hello")
print(value)  # b'world'

# Delete
db.delete(b"hello")
```

### Rust

```rust
// Cargo.toml: rocksdb = "0.23"
use rocksdb::{DB, Options};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let db = DB::open_default("mydb.rocksdb")?;
    db.put(b"hello", b"world")?;
    match db.get(b"hello")? {
        Some(value) => println!("{}", String::from_utf8(value)?),
        None => println!("not found"),
    }
    Ok(())
}
```

## On-Disk Format

LSM-Tree (SST files + Write-Ahead Log)

## Core Strengths

- High write throughput via LSM-tree with leveled and universal compaction
- Low-latency reads with bloom filters and block cache
- Highly tunable -- dozens of knobs for compaction, compression, and memory
- Column families enable logical partitioning within a single database
- Battle-tested at scale across hundreds of Meta services and cloud-native databases

## Best Use Cases

1. **Storage Engine** -- Embed as the persistence layer in a database, message queue, or stream processor.
2. **Data Ingestion Pipelines** -- Absorb high-throughput writes and compact lazily in the background.
3. **Persistent Queues and Event Stores** -- Append-heavy workloads benefit from LSM-tree write optimization.
4. **Local Metadata Storage** -- Fast persistent lookups for configuration, state, and caches in distributed nodes.
5. **Time-Series Append Data** -- Ordered key writes with prefix-based range scans are highly efficient.

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| Python | [`recipe_kv_store.py`](python/src/recipe_kv_store.py) | Basic open, put, get, delete, and iterator scan |
| Python | [`recipe_batch_write.py`](python/src/recipe_batch_write.py) | WriteBatch operations for high-throughput writes |
| Rust | [`recipe_kv_store.rs`](rust/src/bin/recipe_kv_store.rs) | Basic KV operations |
| Rust | [`recipe_batch_write.rs`](rust/src/bin/recipe_batch_write.rs) | WriteBatch operations |

## Limitations & Caveats

- Single-writer by default: only one thread performs writes at a time for consistency. Use TransactionDB for concurrent write transactions.
- Performance tuning requires deep understanding of LSM-tree internals. Defaults are optimized for SSD; spinning disk workloads need significant tuning.
- Embedded-only: no built-in network server. Pair with gRPC or a database protocol layer for remote access.
- Not ACID in the traditional SQL sense. Provides atomic writes within a WriteBatch but no multi-key transactions without TransactionDB.

## Further Reading

- [Official Documentation](https://rocksdb.org)
- [Source Repository](https://github.com/facebook/rocksdb)
- [RocksDB Wiki](https://github.com/facebook/rocksdb/wiki)
- [Performance Benchmarks](https://github.com/facebook/rocksdb/wiki/Performance-Benchmarks)
- [Features Not in LevelDB](https://github.com/facebook/rocksdb/wiki/Features-Not-in-LevelDB)
