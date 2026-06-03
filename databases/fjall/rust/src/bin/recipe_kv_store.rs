//! Recipe: Basic KV Store Operations
//! Database: fjall
//! Description: Demonstrates opening a database, inserting, getting, deleting
//!     keys, and performing prefix scans and range iteration using the fjall
//!     keyspace API.
//!
//! Usage: cargo run --bin recipe_kv_store

use fjall::{Database, KeyspaceCreateOptions, PersistMode};

fn main() -> fjall::Result<()> {
    let dir = tempfile::tempdir()?;
    let db_path = dir.path().join("demo");

    // 1. Setup -- create the database
    let db = Database::builder(&db_path).open()?;
    let items = db.keyspace("kv", || KeyspaceCreateOptions::default())?;

    // 2. Write -- insert key-value pairs
    items.insert("name", b"fjall")?;
    items.insert("type", b"key-value")?;
    items.insert("year", b"2024")?;
    items.insert("license", b"Apache-2.0")?;

    // 3. Read -- retrieve individual keys
    match items.get("name")? {
        Some(bytes) => println!("name = {}", String::from_utf8_lossy(&bytes)),
        None => println!("name = not found"),
    }
    match items.get("type")? {
        Some(bytes) => println!("type = {}", String::from_utf8_lossy(&bytes)),
        None => println!("type = not found"),
    }

    // 4. Delete -- remove a key
    items.remove("license")?;

    match items.get("license")? {
        Some(bytes) => println!("license after delete = {}", String::from_utf8_lossy(&bytes)),
        None => println!("license after delete = None"),
    }

    // 5. Prefix scan -- iterate over entries with a common prefix
    let prefix_items = db.keyspace("prefixed", || KeyspaceCreateOptions::default())?;
    prefix_items.insert("user:1:name", b"Alice")?;
    prefix_items.insert("user:1:email", b"alice@example.com")?;
    prefix_items.insert("user:2:name", b"Bob")?;
    prefix_items.insert("user:2:email", b"bob@example.com")?;

    println!("\nAll entries for user:1:");
    for guard in prefix_items.prefix("user:1") {
        let (key, value) = guard.into_inner()?;
        println!(
            "  {} => {}",
            String::from_utf8_lossy(&key),
            String::from_utf8_lossy(&value)
        );
    }

    // 6. Range iteration
    println!("\nAll entries in range [user, user~):");
    for guard in prefix_items.range("user"..="user~") {
        let (key, value) = guard.into_inner()?;
        println!(
            "  {} => {}",
            String::from_utf8_lossy(&key),
            String::from_utf8_lossy(&value)
        );
    }

    // 7. Durability -- ensure data is persisted to disk
    db.persist(PersistMode::SyncAll)?;

    println!("\nDone.");
    Ok(())
}
