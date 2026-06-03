//! Recipe: Basic KV Store Operations
//! Database: redb
//! Description: Demonstrates opening a database, inserting, getting, deleting
//!     keys, and performing a cursor-based iteration using the redb typed table API.
//!
//! Usage: cargo run --bin recipe_kv_store

use redb::{Database, ReadableDatabase, ReadableTable, TableDefinition};

const TABLE: TableDefinition<&str, &str> = TableDefinition::new("kv");

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let dir = tempfile::tempdir()?;
    let db_path = dir.path().join("demo.redb");

    // 1. Setup -- create the database
    let db = Database::create(&db_path)?;

    // 2. Write -- insert key-value pairs in a write transaction
    let write_txn = db.begin_write()?;
    {
        let mut table = write_txn.open_table(TABLE)?;
        table.insert("name", "redb")?;
        table.insert("type", "key-value")?;
        table.insert("year", "2021")?;
        table.insert("license", "Apache-2.0 OR MIT")?;
    }
    write_txn.commit()?;

    // 3. Read -- retrieve individual keys in a read transaction
    let read_txn = db.begin_read()?;
    let table = read_txn.open_table(TABLE)?;

    match table.get("name")? {
        Some(entry) => println!("name = {}", entry.value()),
        None => println!("name = not found"),
    }
    match table.get("type")? {
        Some(entry) => println!("type = {}", entry.value()),
        None => println!("type = not found"),
    }

    // 4. Delete -- remove a key in a write transaction
    let write_txn = db.begin_write()?;
    {
        let mut table = write_txn.open_table(TABLE)?;
        table.remove("license")?;
    }
    write_txn.commit()?;

    let read_txn = db.begin_read()?;
    let table = read_txn.open_table(TABLE)?;
    match table.get("license")? {
        Some(entry) => println!("license after delete = {}", entry.value()),
        None => println!("license after delete = None"),
    }

    // 5. Scan -- iterate over all entries
    println!("\nAll entries:");
    let read_txn = db.begin_read()?;
    let table = read_txn.open_table(TABLE)?;
    let iter = table.iter()?;
    for result in iter {
        let (key, value) = result?;
        println!("  {} => {}", key.value(), value.value());
    }

    println!("\nDone.");
    Ok(())
}
