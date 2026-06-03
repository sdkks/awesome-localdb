# SlateDB

> **Category:** Key-Value | **License:** Apache-2.0 | **Stars:** ~3,100

## Overview

SlateDB is a cloud-native embedded key-value storage engine built on object storage (S3, MinIO, local filesystem). It implements an LSM-tree architecture that writes data directly to object storage, providing 99.999999999% durability without local disks. SlateDB supports a single-writer, multi-reader deployment model with transactions, snapshots, zero-copy clones, and tunable write durability vs. latency trade-offs.

## Quick Start

### Python

```python
# Install: pip install slatedb
import asyncio
from slatedb.uniffi._slatedb_uniffi import DbBuilder, ObjectStore


async def main():
    # Connect to in-memory object store (or use "s3://bucket" / "file:///path")
    store = ObjectStore.resolve("memory:///")
    builder = DbBuilder("/my-db", store)
    db = await builder.build()

    # Write
    await db.put(b"greeting", b"Hello from SlateDB")

    # Read
    value = await db.get(b"greeting")
    print(f"greeting = {value}")

    # Delete
    await db.delete(b"greeting")

    await db.shutdown()


asyncio.run(main())
```

### Rust

```rust
// Cargo.toml: slatedb = "0.16"
use slatedb::Db;
use slatedb::config::DbOptions;
use slatedb::object_store::memory::InMemory;
use std::sync::Arc;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let store = Arc::new(InMemory::new());
    let options = DbOptions::default();
    let db = Db::open("my-db", store, options).await?;

    db.put(b"greeting", b"Hello from SlateDB").await?;
    let value = db.get(b"greeting").await?;
    println!("greeting = {:?}", value);

    db.close().await?;
    Ok(())
}
```

## On-Disk Format

LSM-Tree (SST files + WAL written to object storage)

## Core Strengths

- Zero-disk architecture: persists directly to S3/MinIO/local object storage
- LSM-tree engine with formally verified manifest fencing protocol
- Single-writer, multi-reader deployment with OCC transactions and snapshots
- Zero-copy clones and branches for O(1) database forking
- Tunable write durability vs. latency for cost-sensitive workloads
- Official bindings for Python, Go, Java, and Node.js via UniFFI

## Best Use Cases

1. **Cloud-Native Services** -- Embed KV storage directly in services running on serverless or containerized platforms without persistent local disks.
2. **Stream Processors** -- Build reliable state stores for stream processing frameworks using object storage as the durability layer.
3. **Feature Stores and Caches** -- Back feature stores and caching layers with object storage for durability while serving reads from local cache.
4. **Custom Databases** -- Use SlateDB as the storage engine when building a custom database, workflow engine, or ledger on top of object storage.
5. **Multi-Reader Analytics** -- Deploy read-only replicas for analytical workloads with snapshot isolation over shared object storage.

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| Python | [`recipe_kv_store.py`](python/src/recipe_kv_store.py) | Basic open, put, get, delete, and list operations |

## Limitations & Caveats

- Single-writer by design: only one writer process at a time. Use the manifest fencing protocol to enforce this in production.
- Write latency is bounded by object storage PUT latency unless you use relaxed durability settings.
- Reads may hit cold-start latency if the local cache is empty; configure cache sizing appropriately.
- The Python package is a UniFFI binding around the Rust core. Native async support requires Python 3.10+.
- Object store consistency varies by backend: S3 and MinIO provide strong read-after-write consistency, but in-memory stores are best-effort.
- Embedded-only: SlateDB does not include a built-in network server or replication protocol.

## Further Reading

- [Official Documentation](https://slatedb.io/docs/get-started/introduction/)
- [Source Repository](https://github.com/slatedb/slatedb)
- [SlateDB Internals Blog Post](https://materializedview.io/p/slatedb-an-embedded-storage-engine)
