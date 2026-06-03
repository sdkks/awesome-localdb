//! Recipe: Basic KV Store Operations
//! Database: RocksDB
//! Description: Demonstrates opening a database, putting, getting, deleting
//!     keys, and performing an iterator scan.
//!
//! Usage: cargo run --bin recipe_kv_store

use rocksdb::{DB, IteratorMode, Options};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let db_path = "/tmp/rocksdb_recipe_kv_store";

    // 1. Setup — open the database
    {
        let db = DB::open_default(db_path)?;

        // 2. Write — insert key-value pairs
        db.put(b"name", b"RocksDB")?;
        db.put(b"type", b"key-value")?;
        db.put(b"year", b"2013")?;
        db.put(b"license", b"Apache-2.0")?;

        // 3. Read — retrieve individual keys
        match db.get(b"name")? {
            Some(value) => println!("name = {}", String::from_utf8(value)?),
            None => println!("name = not found"),
        }
        match db.get(b"type")? {
            Some(value) => println!("type = {}", String::from_utf8(value)?),
            None => println!("type = not found"),
        }

        // 4. Delete — remove a key
        db.delete(b"license")?;
        match db.get(b"license")? {
            Some(value) => println!("license after delete = {}", String::from_utf8(value)?),
            None => println!("license after delete = None"),
        }

        // 5. Scan — iterate over all entries
        println!("\nAll entries:");
        let iter = db.iterator(IteratorMode::Start);
        for item in iter {
            let (key, value) = item?;
            println!(
                "  {} => {}",
                String::from_utf8_lossy(&key),
                String::from_utf8_lossy(&value)
            );
        }
    }

    // 6. Cleanup
    let _ = DB::destroy(&Options::default(), db_path);
    println!("\nDone.");
    Ok(())
}
