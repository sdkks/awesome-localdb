# PoloDB

> **Category:** Document | **License:** Apache-2.0 | **Stars:** ~1,200

## Overview

PoloDB is an embedded document database written in Rust that implements a lightweight MongoDB. It stores data in BSON format over a RocksDB LSM-Tree storage engine, providing a MongoDB-like API with collections, documents, and transactions. PoloDB runs in-process with zero runtime dependencies beyond libc, making it highly portable across platforms. It supports both serde-based typed structs and raw BSON documents via the `polodb_core::bson` re-exported module.

## Quick Start

### Rust

```rust
// Cargo.toml: polodb_core = "5.1"
use polodb_core::{Database, CollectionT};
use polodb_core::bson::{Document, doc};
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
struct Book {
    title: String,
    author: String,
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let db = Database::open_path("mydb.polo")?;

    // Insert with typed struct
    let collection = db.collection::<Book>("books");
    collection.insert_one(Book {
        title: "1984".into(),
        author: "George Orwell".into(),
    })?;

    // Insert with raw BSON document
    let raw_collection = db.collection::<Document>("books");
    raw_collection.insert_one(doc! {
        "title": "Animal Farm",
        "author": "George Orwell",
    })?;

    // Find with filter
    let results = collection.find(doc! {
        "author": "George Orwell"
    })?.run()?;

    for book in results {
        println!("{:?}", book);
    }

    Ok(())
}
```

## On-Disk Format

BSON documents over RocksDB LSM-Tree (single file)

## Core Strengths

- MongoDB-like API with collections, documents, and find queries
- BSON-native storage with `polodb_core::bson` re-export and serde support
- Zero runtime dependencies beyond libc, highly portable across platforms
- Explicit transaction control with auto-transaction fallback per operation
- Single-file storage format, simple to deploy and back up
- Cross-platform including iOS and Android via Rust cross-compilation

## Best Use Cases

1. **Rust Desktop Apps** -- Embed MongoDB-like document storage directly in Tauri, egui, or Iced apps without a standalone server.
2. **Mobile Apps (iOS/Android)** -- Use PoloDB as an embedded document database in Rust-backed mobile applications.
3. **CLI Tools** -- Persist configuration, state, and structured data in schemaless format for single-binary Rust tools.
4. **Local-First Prototyping** -- Develop locally with a MongoDB-compatible API before scaling to a full MongoDB deployment.
5. **Edge and IoT Devices** -- Minimal dependency footprint makes PoloDB suitable for resource-constrained environments.

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| Rust | [`recipe_document_store.rs`](rust/src/bin/recipe_document_store.rs) | CRUD operations with typed structs and BSON documents, transactions, find with filters |

## Limitations & Caveats

- Uses RocksDB internally, which requires a C++ toolchain to compile from source. Cross-compilation for mobile targets may require pre-built RocksDB binaries.
- The API is MongoDB-inspired but not wire-compatible. It is an embedded library, not a drop-in MongoDB replacement.
- BSON is the native document format. JSON data must be serialized to BSON on write and deserialized on read.
- Write operations require `serde::Serialize` and read operations require `serde::Deserialize` on document types.
- Single-writer by design (RocksDB constraint). Concurrent reads are supported but writes are serialized.
- Embedded-only: no built-in network server, replication, or clustering protocol. The separate `polodb` crate provides an optional MongoDB-wire-protocol-compatible server for networked access.

## Further Reading

- [Official Documentation](https://www.polodb.org/docs)
- [Source Repository](https://github.com/PoloDB/PoloDB)
- [docs.rs / polodb_core](https://docs.rs/polodb_core)
- [Why PoloDB?](https://www.polodb.org/docs/why.html)
