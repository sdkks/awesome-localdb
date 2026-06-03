# buntdb

> **Category:** Key-Value | **License:** MIT | **Stars:** ~5,000

## Overview

buntdb is an embeddable, in-memory key/value database for Go with custom indexing and geospatial support. It persists data to disk via an append-only file, supports ACID transactions with multiple concurrent readers and a single writer, and provides B-tree and R-tree indexes for ordering, iteration, and spatial queries. JSON field indexing is powered by GJSON, enabling indexes on nested document fields.

## Quick Start

### Go

```go
package main

import (
	"fmt"
	"log"

	"github.com/tidwall/buntdb"
)

func main() {
	// Open an in-memory database
	db, err := buntdb.Open(":memory:")
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	// Write in a read-write transaction
	db.Update(func(tx *buntdb.Tx) error {
		tx.Set("user:1", "alice", nil)
		tx.Set("user:2", "bob", nil)
		tx.Set("user:3", "carol", nil)
		return nil
	})

	// Read in a read-only transaction
	db.View(func(tx *buntdb.Tx) error {
		val, err := tx.Get("user:1")
		if err != nil {
			return err
		}
		fmt.Printf("user:1 = %s\n", val)
		return nil
	})

	// Iterate with a custom index
	db.CreateIndex("names", "user:*", buntdb.IndexString)
	db.View(func(tx *buntdb.Tx) error {
		tx.Ascend("names", func(key, value string) bool {
			fmt.Printf("%s: %s\n", key, value)
			return true // continue iteration
		})
		return nil
	})
}
```

## On-Disk Format

Append-only file (AOF) with auto-shrink compaction

## Core Strengths

- In-memory speed with ACID durability via append-only file persistence
- Custom B-tree indexes for ordered iteration and range queries over values
- Spatial indexing with R-trees supporting up to 20 dimensions and kNN queries
- JSON field indexing via GJSON for querying nested document structures
- TTL-based expiration for automatic item eviction without manual cleanup
- Zero external dependencies beyond standard Go packages and sibling tidwall libraries

## Best Use Cases

1. **Embedded K/V Store** -- Add in-memory key/value storage with optional disk persistence to Go applications.
2. **Local Caching Layer** -- Use TTL-based expiration with durable recovery for application caches that survive restarts.
3. **Geospatial Applications** -- Fast spatial intersection and k-nearest neighbor queries via built-in R-tree indexes.
4. **JSON Document Indexing** -- Store JSON values and index nested fields for queryable document storage.
5. **Ordered Iteration** -- Leverage B-tree indexes for efficient range scans and ordered traversal over keys.

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| Go | [`recipe_kv_store`](go/cmd/recipe_kv_store/main.go) | Open, set, get, delete, index iteration, spatial query, and TTL |

## Limitations & Caveats

- Entire dataset is held in memory; available RAM limits the dataset size. Not suitable for datasets exceeding memory capacity.
- Single-writer design: only one writer at a time, enforced via internal locking. Multiple concurrent readers are allowed.
- The append-only file grows over time; auto-shrink compaction must be configured appropriately for production use.
- buntdb is not a distributed database. For multi-node deployments, combine it with replication at the application layer.
- Spatial indexes are approximate for non-rectangular shapes; use bounding-box intersection as a pre-filter.

## Further Reading

- [Source Repository](https://github.com/tidwall/buntdb)
- [Go Package Documentation](https://pkg.go.dev/github.com/tidwall/buntdb)
- [BuntDB Performance Benchmarks](https://github.com/tidwall/buntdb#performance)
