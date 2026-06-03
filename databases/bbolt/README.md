# bbolt

> **Category:** Key-Value | **License:** MIT | **Stars:** ~9,500

## Overview

bbolt is the maintained community fork of BoltDB, an embedded key/value database for Go. It stores data in a single memory-mapped file using a B+Tree structure, providing fully serializable ACID transactions with MVCC via copy-on-write semantics. bbolt powers etcd, the distributed key-value store that underpins the Kubernetes control plane.

## Quick Start

### Go

```go
package main

import (
	"log"
	bolt "go.etcd.io/bbolt"
)

func main() {
	// Open (creates if missing)
	db, err := bolt.Open("my.db", 0600, nil)
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	// Write in a read-write transaction
	db.Update(func(tx *bolt.Tx) error {
		b, err := tx.CreateBucketIfNotExists([]byte("users"))
		if err != nil {
			return err
		}
		return b.Put([]byte("alice"), []byte("admin"))
	})

	// Read in a read-only transaction
	db.View(func(tx *bolt.Tx) error {
		b := tx.Bucket([]byte("users"))
		v := b.Get([]byte("alice"))
		log.Printf("alice: %s\n", v)
		return nil
	})
}
```

## On-Disk Format

B+Tree memory-mapped (single file)

## Core Strengths

- Pure Go implementation with zero external dependencies and under 5 KLOC
- ACID transactions with serializable isolation via copy-on-write
- Memory-mapped B+Tree enabling zero-copy reads from the OS buffer cache
- Concurrent readers never block; writes serialized through a file-level lock
- Nested bucket support for logical key-space partitioning and namespacing

## Best Use Cases

1. **Embedded Metadata Storage** -- Store configuration, indexes, and application state in Go programs without external dependencies.
2. **Persistent Cache** -- Survive process restarts with a durable, transactional local cache.
3. **Distributed System Backend** -- Use as a building block for distributed stores, as etcd does with Kubernetes.
4. **Learning K/V Internals** -- Study a clean, compact transaction-based storage engine (under 5 KLOC).
5. **Single-File Persistence** -- Ship applications that need durable state in a single portable file.

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| Go | [`recipe_kv_store`](go/cmd/recipe_kv_store/main.go) | Basic open, put, get, delete, and cursor scan |
| Go | [`recipe_bucket_operations`](go/cmd/recipe_bucket_operations/main.go) | Nested buckets, namespace partitioning, and bucket iteration |

## Limitations & Caveats

- Single-writer by design: only one writer at a time, enforced via file-level lock. Multiple concurrent readers are allowed.
- The database file must be opened by a single process; sharing across processes requires opening read-only or OS-level coordination.
- Keys within a bucket are lexicographically sorted by byte value. Long keys and large values share the same B+Tree page structure.
- bbolt is not a distributed database. For multi-node coordination, users compose it with Raft (as etcd does).

## Further Reading

- [Source Repository](https://github.com/etcd-io/bbolt)
- [Go Package Documentation](https://pkg.go.dev/go.etcd.io/bbolt)
- [bbolt Comparison to Other Databases](https://github.com/etcd-io/bbolt#comparison-to-other-databases)
- [etcd Documentation](https://etcd.io/docs/)
