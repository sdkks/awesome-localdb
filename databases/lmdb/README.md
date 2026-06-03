# LMDB

> **Category:** Key-Value | **License:** OpenLDAP Public License | **Stars:** ~2,000

## Overview

LMDB (Lightning Memory-Mapped Database) is an ultra-fast, compact, embedded key-value store that uses memory-mapped files with a B+Tree design. It provides fully ACID transactions with MVCC (Multi-Version Concurrency Control), allowing concurrent readers to operate without blocking a single writer. LMDB is ideal for applications requiring minimal overhead, high read performance, and predictable latency -- widely used in OpenLDAP, cryptocurrency nodes, and as a storage backend in distributed systems.

## Quick Start

### Python

```python
# Install: pip install lmdb
import lmdb

# Open — map_size sets the maximum database size (1 GB here)
env = lmdb.open("mydb.lmdb", map_size=1024 * 1024 * 1024)

# Write
with env.begin(write=True) as txn:
    txn.put(b"greeting", b"Hello from LMDB")
    txn.put(b"language", b"Python")

# Read
with env.begin() as txn:
    value = txn.get(b"greeting")
    print(value)  # b'Hello from LMDB'

# Iterate
with env.begin() as txn:
    with txn.cursor() as cursor:
        for key, value in cursor:
            print(f"{key.decode()} => {value.decode()}")

env.close()
```

### Rust

```rust
// Cargo.toml: heed = "0.22"
use heed::{EnvOpenOptions, Database};
use heed::types::Str;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let dir = tempfile::tempdir()?;
    let env = unsafe { EnvOpenOptions::new().max_dbs(1).open(dir.path())? };

    let mut wtxn = env.write_txn()?;
    let db: Database<Str, Str> = env.create_database(&mut wtxn, None)?;
    db.put(&mut wtxn, "greeting", "Hello from LMDB")?;
    wtxn.commit()?;

    let rtxn = env.read_txn()?;
    match db.get(&rtxn, "greeting")? {
        Some(value) => println!("greeting = {}", value),
        None => println!("not found"),
    }
    Ok(())
}
```

## On-Disk Format

B+Tree memory-mapped (single data file + lock file)

## Core Strengths

- MVCC with concurrent readers that never block a single writer
- Zero-copy reads via memory-mapped files, fully exploiting the OS buffer cache
- ACID transactions with full crash recovery via copy-on-write
- Extremely compact -- the library itself is ~40 KB of tightly optimized C
- Deterministic read latency with no background compaction threads

## Best Use Cases

1. **High-Concurrency Reads** -- Thousands of concurrent readers with zero contention on a single writer. Ideal for read-heavy services.
2. **Embedded Metadata Storage** -- Lightweight configuration and state storage in long-running daemons and microservices.
3. **Local Caching Layers** -- Fast, persistent key-value lookups where RocksDB-level tuning is unnecessary overhead.
4. **Cryptocurrency Nodes** -- Proven storage engine for blockchain applications requiring deterministic performance.
5. **Directory Services** -- The original use case: OpenLDAP's MDB backend uses LMDB for sub-millisecond reads.

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| Python | [`recipe_kv_store.py`](python/src/recipe_kv_store.py) | Basic open, put, get, delete, and cursor iteration |
| Python | [`recipe_concurrent_readers.py`](python/src/recipe_concurrent_readers.py) | Demonstrates MVCC with multiple concurrent readers |
| Rust | [`recipe_kv_store.rs`](rust/src/bin/recipe_kv_store.rs) | Basic KV operations with typed database |

## Limitations & Caveats

- Single-writer by design: only one write transaction at a time. Writes are serialized.
- The database is memory-mapped at a fixed virtual address size. You must set `map_size` large enough up front.
- The default map size on 64-bit is a conservative 1 MB. Increase it before inserting significant data.
- No write-ahead log -- a crash during a write transaction rolls back to the last committed state automatically.
- Keys are lexicographically sorted. Prefix scans are efficient; range queries require full scan unless keys are designed with prefixes.
- Embedded-only: no built-in network server. Pair with a protocol layer for remote access.

## Further Reading

- [Official Documentation](https://www.lmdb.tech/doc/)
- [Source Repository](https://github.com/LMDB/lmdb)
- [LMDB Technical Overview](https://symas.com/lmdb/technical/)
- [Microbenchmarks](https://www.lmdb.tech/bench/microbench/)
- [Mozilla RKV Evaluation (LMDB vs SQLite vs RocksDB)](https://mozilla.github.io/firefox-browser-architecture/text/0015-rkv.html)
