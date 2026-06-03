# LevelDB

> **Category:** Key-Value | **License:** BSD-3-Clause | **Stars:** ~37,000

## Overview

LevelDB is a fast, lightweight key-value storage library written at Google that provides an ordered mapping from string keys to string values. It uses a Log-Structured Merge-Tree (LSM-Tree) design for high write throughput and efficient range scans. Designed as a foundational building block rather than a full database, LevelDB is embedded directly into applications and has inspired numerous derivatives including RocksDB and HyperLevelDB.

## Quick Start

### Python

```python
# Install: pip install plyvel
import plyvel

# Open (creates if missing)
db = plyvel.DB("/tmp/mydb.leveldb", create_if_missing=True)

# Write
db.put(b"hello", b"world")

# Read
value = db.get(b"hello")
print(value)  # b'world'

# Delete
db.delete(b"hello")

# Close
db.close()
```

## On-Disk Format

LSM-Tree (SSTable files + Write-Ahead Log)

## Core Strengths

- Lightweight binary with small memory footprint ideal for embedded use
- Simple LSM-tree design with predictable write and read performance
- Ordered key space enables efficient range scans and prefix iteration
- Snappy compression reduces disk usage with minimal CPU overhead
- Battle-tested foundation for Chrome, Bigtable, and many derivative stores

## Best Use Cases

1. **Local Persistent Storage** -- Embed key-value storage in desktop applications, mobile apps, and CLI tools.
2. **Storage Engine Foundation** -- Use as the persistence layer when building a custom database or index.
3. **Metadata and Index Storage** -- Store configuration, state, and lookup tables where simplicity matters.
4. **Learning LSM-Tree Internals** -- Study a clean, minimal reference implementation of LSM-tree principles.
5. **Embedded Storage** -- Ship as a dependency in lightweight daemons or single-purpose services.

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| Python | [`recipe_kv_store.py`](python/src/recipe_kv_store.py) | Basic open, put, get, delete, and iterator scan |
| Python | [`recipe_batch_operations.py`](python/src/recipe_batch_operations.py) | Atomic write batches for high-throughput writes |

## Limitations & Caveats

- Single-writer by design: only one process may open a database at a time, enforced via filesystem lock.
- No built-in replication, sharding, transactions, or SQL. LevelDB is purely a key-value store.
- Development is slow as Google considers LevelDB feature-complete and stable. Active forks like RocksDB add more features.
- The C++ API is minimal by design. Python users should use the `plyvel` binding for a full-featured interface.

## Further Reading

- [Source Repository](https://github.com/google/leveldb)
- [LevelDB Benchmarks](https://github.com/google/leveldb/blob/main/doc/benchmark.md)
- [LevelDB Documentation (doc/index.md)](https://github.com/google/leveldb/blob/main/doc/index.md)
- [Features Not in LevelDB (RocksDB comparison)](https://github.com/facebook/rocksdb/wiki/Features-Not-in-LevelDB)
