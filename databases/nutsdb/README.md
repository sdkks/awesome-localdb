# NutsDB

> **Category:** Key-Value | **License:** Apache-2.0 | **Stars:** ~4,000

## Overview

NutsDB is a simple, fast, embeddable, persistent key/value store written in pure Go. It supports fully serializable transactions and Redis-like data structures including lists, sets, and sorted sets. Inspired by the Bitcask model, NutsDB uses an append-only log for writes with in-memory index structures for fast lookups. All operations happen inside transactions, making it an ideal embedded database for Go applications that need more than a basic key-value store.

## Quick Start

### Go

```go
package main

import (
    "log"

    "github.com/nutsdb/nutsdb"
)

func main() {
    // Open the database (creates if missing)
    db, err := nutsdb.Open(
        nutsdb.DefaultOptions,
        nutsdb.WithDir("/tmp/nutsdb"),
    )
    if err != nil {
        log.Fatal(err)
    }
    defer db.Close()

    // Create a bucket and write data
    db.Update(func(tx *nutsdb.Tx) error {
        tx.NewBucket(nutsdb.DataStructureBTree, "users")
        return tx.Put("users", []byte("alice"), []byte("engineer"), 0)
    })

    // Read data
    db.View(func(tx *nutsdb.Tx) error {
        val, err := tx.Get("users", []byte("alice"))
        if err != nil {
            return err
        }
        log.Printf("alice: %s\n", val)
        return nil
    })
}
```

## On-Disk Format

Bitcask-inspired append-only log with multiple data files and in-memory indexes

## Core Strengths

- Pure Go implementation with zero external dependencies
- Redis-like data structures: list, set, sorted set natively
- Fully serializable ACID transactions with read-only and read-write modes
- TTL support with automatic expiration of keys
- Merge V2 compaction and HintFile for fast startup and reduced memory
- Watch key changes for real-time data monitoring

## Best Use Cases

1. **Embedded Data Structures** -- Use lists, sets, and sorted sets natively in Go applications without Redis.
2. **Local Caching with TTL** -- Store cached data with automatic expiration for Go services and CLI tools.
3. **Lightweight Redis Replacement** -- Replace Redis for single-process Go apps that need data structures.
4. **Metadata and Configuration Storage** -- Persist application config and metadata with ACID transactions.
5. **Ordered Key-Value Access** -- Leverage prefix scans and range queries on sorted keys.

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| Go | [`recipe_kv_store`](go/cmd/recipe_kv_store/main.go) | Basic open, bucket creation, put, get, delete, and iteration |

## Limitations & Caveats

- Buckets must be created explicitly before use and are tied to a data structure type (BTree, List, Set, SortedSet).
- Starting from v1.0.0, the underlying data storage protocol changed; old-version data is not compatible.
- The Bitcask-based storage model means the entire key index is held in memory; very large key counts may use significant RAM.
- Write operations are serialized through transactions; high-concurrency write workloads may need batching.
- Requires Go 1.18+.

## Further Reading

- [Source Repository](https://github.com/nutsdb/nutsdb)
- [NutsDB Documentation](https://nutsdb.github.io/nutsdb-docs/)
- [Go Package Documentation](https://pkg.go.dev/github.com/nutsdb/nutsdb)
- [Comparison to Other Databases](https://github.com/nutsdb/nutsdb/blob/master/docs/user_guides/comparison.md)
