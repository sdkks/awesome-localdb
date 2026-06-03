//! Recipe: Typed Tables with Multiple Data Types
//! Database: redb
//! Description: Demonstrates using multiple TableDefinitions with different
//!     Rust types, including integers and strings, plus range queries.
//!
//! Usage: cargo run --bin recipe_typed_tables

use redb::{
    Database, Range, ReadableDatabase, ReadableTable, ReadableTableMetadata, TableDefinition,
};

const USERS_TABLE: TableDefinition<u64, &str> = TableDefinition::new("users");

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let dir = tempfile::tempdir()?;
    let db_path = dir.path().join("typed.redb");

    // 1. Setup -- create the database
    let db = Database::create(&db_path)?;

    // 2. Write -- insert typed records
    let write_txn = db.begin_write()?;
    {
        let mut table = write_txn.open_table(USERS_TABLE)?;
        table.insert(1, "Alice")?;
        table.insert(2, "Bob")?;
        table.insert(3, "Carol")?;
        table.insert(4, "Dave")?;
        table.insert(5, "Eve")?;
    }
    write_txn.commit()?;

    // 3. Read -- point lookup by integer key
    let read_txn = db.begin_read()?;
    let table = read_txn.open_table(USERS_TABLE)?;

    match table.get(3)? {
        Some(entry) => println!("User 3 = {}", entry.value()),
        None => println!("User 3 not found"),
    }

    // 4. Range query -- iterate over users 2..4 (exclusive end)
    println!("\nUsers in range [2, 4):");
    let range: Range<u64, &str> = table.range(2..4)?;
    for result in range {
        let (key, value) = result?;
        println!("  {} => {}", key.value(), value.value());
    }

    // 5. Full scan
    println!("\nAll users:");
    let iter = table.iter()?;
    for result in iter {
        let (key, value) = result?;
        println!("  {} => {}", key.value(), value.value());
    }

    // 6. Count entries
    let count = table.len()?;
    println!("\nTotal users: {}", count);

    println!("\nDone.");
    Ok(())
}
