//! Recipe: WriteBatch Operations
//! Database: RocksDB
//! Description: Demonstrates using WriteBatch for high-throughput atomic writes,
//!     batching multiple puts and deletes in a single commit.
//!
//! Usage: cargo run --bin recipe_batch_write

use rocksdb::{DB, Options, WriteBatch};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let db_path = "/tmp/rocksdb_recipe_batch_write";

    // 1. Setup — open the database
    {
        let db = DB::open_default(db_path)?;

        // 2. WriteBatch — stage multiple operations atomically
        let mut batch = WriteBatch::default();
        for i in 1..=5 {
            let key = format!("item:{}", i);
            let value = format!("value-{}", i);
            batch.put(key.as_bytes(), value.as_bytes());
        }
        batch.delete(b"item:3"); // Remove item:3 from the batch
        db.write(batch)?;

        // 3. Read back — verify batch results
        println!("After WriteBatch:");
        for i in 1..=5 {
            let key = format!("item:{}", i);
            match db.get(key.as_bytes())? {
                Some(value) => println!("  {} => {}", key, String::from_utf8(value)?),
                None => println!("  {} => (deleted)", key),
            }
        }
    }

    // 4. Cleanup
    let _ = DB::destroy(&Options::default(), db_path);
    println!("\nDone.");
    Ok(())
}
