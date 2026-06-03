# Sanakirja

> **Category:** Key-Value | **License:** Apache-2.0 | **Crate:** [sanakirja](https://crates.io/crates/sanakirja)

## Overview

Sanakirja (Finnish for "dictionary") is a transactional, on-disk key-value store backed by copy-on-write B-trees, written in pure Rust. Originally developed as the storage engine for the Pijul version control system, it provides concurrent readers and writers through a multi-version architecture where readers see a consistent snapshot without blocking writers. It is split into a `#[no_std]` core crate (`sanakirja-core`) with a generic allocator, and a higher-level crate (`sanakirja`) with memory-mapped file support. Sanakirja is production-proven, having powered every Pijul repository since 2016, and benchmarks 20-50% faster than LMDB for its primary workload of storing version control graphs.

## Quick Start

### Rust

```rust
// Cargo.toml: sanakirja = "1.4"
use sanakirja::*;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let dir = tempfile::tempdir()?;
    let path = dir.path().join("mydb");

    // Create environment: 1 MiB initial size, 2 concurrent versions
    let env = Env::new(&path, 1 << 20, 2)?;

    // Write
    let mut txn = Env::mut_txn_begin(&env)?;
    let mut db: btree::Db<u64, u64> = unsafe { btree::create_db::<_, u64, u64>(&mut txn)? };
    btree::put(&mut txn, &mut db, &1, &100)?;
    btree::put(&mut txn, &mut db, &2, &200)?;
    txn.set_root(0, db.db.into());
    txn.commit()?;

    // Read
    let txn = Env::txn_begin(&env)?;
    let db: btree::Db<u64, u64> = txn.root_db(0).ok_or("root_db not found")?;
    if let Some((k, v)) = btree::get(&txn, &db, &1, None)? {
        println!("key {} = {}", k, v);
    }

    Ok(())
}
```

## On-Disk Format

Copy-on-Write B-Tree (4096-byte pages, multi-version root pages, single file)

## Core Strengths

- Copy-on-write B-trees with concurrent readers that never block on writers
- Benchmarked 20-50% faster than LMDB for graph-storage workloads (u64 key-value)
- Reference-counted page sharing enables near-zero-cost table forks
- `#[no_std]` core crate with generic allocator -- usable beyond filesystems
- Production-proven as the storage engine for Pijul VCS since 2016
- Statically-typed keys and values with zero-copy reads for sized types

## Best Use Cases

1. **Version Control Systems** -- Sanakirja's page-level reference counting makes it ideal for CRDT-backed applications that need cheap, copy-on-write table forking.
2. **Rust Embedded KV Store** -- A drop-in LMDB alternative for Rust applications that need a high-performance transactional B-tree.
3. **Graph-Structured Data** -- Reference-counted page sharing eliminates copies when storing graph relationships that share sub-trees.
4. **Systems Programming** -- `#[no_std]` compatibility with a custom allocator trait lets you store B-trees on raw block devices or custom storage backends.
5. **High-Throughput Writes** -- The copy-on-write design avoids the compaction overhead of LSM-tree engines on write-heavy workloads.

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| Rust | [`recipe_kv_store.rs`](rust/src/bin/recipe_kv_store.rs) | Basic open, insert, get, delete, and cursor iteration |

## Limitations & Caveats

- Single-writer by design: only one mutable transaction at a time.
- The number of concurrent versions is fixed at database creation. A long-running reader on the oldest version can block writers.
- The API is lower-level than typical Rust KV stores: users manage root pointers manually via `set_root`/`root_db`, and `btree::create_db` is `unsafe`.
- `btree::get` returns the first entry with key >= the search key (B-tree seek semantics), not an exact match. Always compare the returned key.
- The on-disk format may not be stable across major versions (1.x to 2.x). Version 2.0.0-beta introduces a new storage architecture.
- The default page size is 4096 bytes; keys and values are limited by available page space.
- The repository is hosted on [nest.pijul.com](https://nest.pijul.com/pijul/sanakirja) (Pijul's own VCS platform), not GitHub.

## Further Reading

- [Official Documentation (docs.rs)](https://docs.rs/sanakirja/latest/sanakirja/)
- [Source Repository (nest.pijul.com)](https://nest.pijul.com/pijul/sanakirja)
- [Crate on crates.io](https://crates.io/crates/sanakirja)
- [Rethinking Sanakirja (blog post with benchmarks)](https://pijul.org/posts/2021-02-06-rethinking-sanakirja/)
- [Compressed Sanakirja Databases](https://pijul.org/posts/sanakirja-zstd/)
