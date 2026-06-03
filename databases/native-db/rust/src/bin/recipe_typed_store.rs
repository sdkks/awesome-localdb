//! Recipe: Typed Store with Model Migration
//! Database: Native DB
//! Description: Demonstrates defining Rust structs as database models with primary
//!     and secondary keys, CRUD operations (insert, get, scan, upsert, update, remove),
//!     and automatic model migration between versions using the native_model crate.
//!
//! Usage: cargo run --bin recipe_typed_store

use native_db::*;
use native_model::{native_model, Model};
use once_cell::sync::Lazy;
use serde::{Deserialize, Serialize};

// ─── Model v1 ────────────────────────────────────────────────────────────

#[derive(Serialize, Deserialize, PartialEq, Debug, Clone)]
#[native_model(id = 1, version = 1)]
#[native_db]
struct ProductV1 {
    #[primary_key]
    sku: u32,
    #[secondary_key]
    name: String,
}

// ─── Model v2 (adds price and category) ──────────────────────────────────

#[derive(Serialize, Deserialize, PartialEq, Debug, Clone)]
#[native_model(id = 1, version = 2, from = ProductV1)]
#[native_db]
struct ProductV2 {
    #[primary_key]
    sku: u32,
    #[secondary_key]
    name: String,
    price: f64,
    category: String,
}

impl From<ProductV1> for ProductV2 {
    fn from(v1: ProductV1) -> Self {
        Self {
            sku: v1.sku,
            name: v1.name,
            price: 0.0,
            category: "uncategorized".to_string(),
        }
    }
}

// Required by native_model for bidirectional version conversion
impl From<ProductV2> for ProductV1 {
    fn from(v2: ProductV2) -> Self {
        Self {
            sku: v2.sku,
            name: v2.name,
        }
    }
}

// Current version alias
type Product = ProductV2;

// ─── Models registry ─────────────────────────────────────────────────────

static MODELS: Lazy<Models> = Lazy::new(|| {
    let mut models = Models::new();
    models.define::<ProductV1>().unwrap();
    models.define::<ProductV2>().unwrap();
    models
});

// ─── Main ────────────────────────────────────────────────────────────────

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let dir = tempfile::tempdir()?;
    let db_path = dir.path().join("store.db");

    // 1. Setup — create persistent database on disk
    let db = Builder::new().create(&MODELS, &db_path)?;

    // 2. Insert products (v1)
    let rw = db.rw_transaction()?;
    rw.insert(ProductV1 {
        sku: 100,
        name: "Widget".to_string(),
    })?;
    rw.insert(ProductV1 {
        sku: 101,
        name: "Gadget".to_string(),
    })?;
    rw.insert(ProductV1 {
        sku: 102,
        name: "Gizmo".to_string(),
    })?;
    rw.commit()?;

    // 3. Read — get by primary key
    let r = db.r_transaction()?;
    let product: ProductV1 = r.get().primary(101_u32)?.unwrap();
    println!("Got by PK: {:?}", product);

    // 4. Scan — iterate all products (v1)
    let r = db.r_transaction()?;
    println!("\nAll products (version 1):");
    for item in r.scan().primary::<ProductV1>()?.all()? {
        println!("  {:?}", item);
    }

    // 5. Migrate — v1 → v2 with automatic model migration
    let rw = db.rw_transaction()?;
    rw.migrate::<Product>()?;
    rw.commit()?;

    // Read back migrated data
    let r = db.r_transaction()?;
    println!("\nAfter migration (version 2):");
    for item in r.scan().primary::<Product>()?.all()? {
        println!("  {:?}", item);
    }

    // 6. Upsert — insert-or-update (v2)
    let rw = db.rw_transaction()?;
    rw.upsert(Product {
        sku: 100,
        name: "Widget Pro".to_string(),
        price: 19.99,
        category: "tools".to_string(),
    })?;
    rw.commit()?;

    // 7. Update — read current value, then replace
    let r = db.r_transaction()?;
    let old_gizmo: Product = r.get().primary(102_u32)?.unwrap();
    drop(r);

    let rw = db.rw_transaction()?;
    rw.update(
        old_gizmo.clone(),
        Product {
            sku: 102,
            name: "Gizmo Deluxe".to_string(),
            price: 14.99,
            category: "gadgets".to_string(),
        },
    )?;
    rw.commit()?;

    // 8. Read — verify migrated and updated data
    let r = db.r_transaction()?;
    println!("\nAll products (version 2):");
    for item in r.scan().primary::<Product>()?.all()? {
        println!("  {:?}", item);
    }

    // 9. Scan by secondary key — find products by name prefix
    let r = db.r_transaction()?;
    println!("\nProducts starting with 'G':");
    for item in r
        .scan()
        .secondary::<Product>(ProductV2Key::name)?
        .start_with("G")?
    {
        println!("  {:?}", item);
    }

    // 10. Scan by secondary key — range query on name
    let r = db.r_transaction()?;
    println!("\nProducts in name range 'G'..='W':");
    for item in r
        .scan()
        .secondary::<Product>(ProductV2Key::name)?
        .range("G".to_string()..="W".to_string())?
    {
        println!("  {:?}", item);
    }

    // 11. Count items
    let r = db.r_transaction()?;
    let count = r.len().primary::<Product>()?;
    println!("\nTotal products: {}", count);

    // 12. Remove — delete the first product
    let r = db.r_transaction()?;
    let to_remove: Product = r.get().primary(100_u32)?.unwrap();
    drop(r);

    let rw = db.rw_transaction()?;
    rw.remove(to_remove)?;
    rw.commit()?;

    let r = db.r_transaction()?;
    let remaining = r.len().primary::<Product>()?;
    println!("After delete, total products: {}", remaining);

    // 13. Verify removed item is gone
    let result: Option<Product> = r.get().primary(100_u32)?;
    println!("Product 100 after delete: {:?}", result);

    println!("\nDone.");
    Ok(())
}
