# Native DB

> **Category:** Document | **License:** MIT | **Stars:** ~700

## Overview

Native DB is a drop-in, fast, embedded database for multi-platform Rust apps (server, desktop, mobile). It maintains coherence between Rust types and stored data with minimal boilerplate, using the native_model crate for transparent serialization/deserialization with any serde-compatible format. Native DB supports multiple indexes (primary, secondary, unique, non-unique, optional), ACID transactions via redb, automatic model migration, real-time watch subscriptions with filters, and hot snapshots. Designed for Rust developers who want type-safe persistence without defining schemas separately from their data types.

## Quick Start

### Rust

```rust
// Cargo.toml: native_db = "0.8", native_model = "0.4"
use native_db::*;
use native_model::{native_model, Model};
use once_cell::sync::Lazy;
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, PartialEq, Debug)]
#[native_model(id = 1, version = 1)]
#[native_db]
struct Item {
    #[primary_key]
    id: u32,
    #[secondary_key]
    name: String,
}

static MODELS: Lazy<Models> = Lazy::new(|| {
    let mut models = Models::new();
    models.define::<Item>().unwrap();
    models
});

fn main() -> Result<(), db_type::Error> {
    let mut db = Builder::new().create_in_memory(&MODELS)?;

    // Insert
    let rw = db.rw_transaction()?;
    rw.insert(Item { id: 1, name: "red".to_string() })?;
    rw.insert(Item { id: 2, name: "green".to_string() })?;
    rw.insert(Item { id: 3, name: "blue".to_string() })?;
    rw.commit()?;

    // Read by primary key
    let r = db.r_transaction()?;
    let item: Item = r.get().primary(3_u32)?.unwrap();
    println!("item id=3: {:?}", item);

    // Scan by secondary key prefix
    for item in r.scan().secondary::<Item>(ItemKey::name)?.start_with("red")? {
        println!("name starts with 'red': {:?}", item);
    }

    Ok(())
}
```

## On-Disk Format

redb (B-tree pages, single-file database)

## Core Strengths

- Zero-schema persistence -- Rust structs are the schema, no DDL or ORM mapping
- Type-safe queries via Rust generics, preventing mismatch between query key type and model
- Automatic model migration with versioned data types and From trait-based conversion
- Multiple index types: primary, secondary, unique, non-unique, and optional indexes
- ACID transactions backed by redb with read-write and read-only transaction modes
- Real-time watch subscriptions with filters for insert, update, and delete events
- Hot snapshots for backup without stopping the database

## Best Use Cases

1. **Desktop Apps** -- Use Native DB in Tauri, egui, or iced apps for typed local persistence without SQL.
2. **Mobile Rust Apps** -- Target iOS and Android with an embedded database that cross-compiles cleanly.
3. **CLI Tool State** -- Store structured configuration, caches, and incremental state with automatic migration.
4. **IoT and Embedded** -- Type-coherent local storage for single-user devices and embedded systems.
5. **Rust-First Applications** -- When your entire data model is defined as Rust types and you want zero mapping overhead.

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| Rust | [`recipe_typed_store.rs`](rust/src/bin/recipe_typed_store.rs) | Model definition, insert, get, scan, upsert, update, remove, and migration |

## Limitations & Caveats

- Embedded-only: no network server, replication protocol, or clustering support.
- Single-writer, multiple-reader concurrency model -- only one write transaction at a time.
- No SQL or query language -- all data access is through the typed Rust API.
- The API is still evolving and may have breaking changes between minor versions.
- Schema migration requires manual implementation of From traits for version transitions.
- Not suitable for multi-process access to the same database file.

## Further Reading

- [API Documentation (docs.rs)](https://docs.rs/native_db)
- [Source Repository](https://github.com/vincent-herlemont/native_db)
- [native_model Crate](https://crates.io/crates/native_model)
- [Benchmarks (vs SQLite and redb)](https://github.com/vincent-herlemont/native_db/blob/main/benches/README.md)
- [Tauri Example](https://github.com/vincent-herlemont/native_db_tauri_vanilla)
