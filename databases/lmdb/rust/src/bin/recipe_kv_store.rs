//! Recipe: Basic KV Store Operations
//! Database: LMDB
//! Description: Demonstrates opening an environment, putting, getting, deleting
//!     keys, and performing a cursor-based iteration using the heed crate.
//!
//! Usage: cargo run --bin recipe_kv_store

use heed::types::Str;
use heed::{Database, EnvOpenOptions};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let dir = tempfile::tempdir()?;

    // 1. Setup — open the environment
    let env = unsafe { EnvOpenOptions::new().max_dbs(1).open(dir.path())? };

    // 2. Write — insert key-value pairs in a write transaction
    let mut wtxn = env.write_txn()?;
    let db: Database<Str, Str> = env.create_database(&mut wtxn, None)?;

    db.put(&mut wtxn, "name", "LMDB")?;
    db.put(&mut wtxn, "type", "key-value")?;
    db.put(&mut wtxn, "year", "2011")?;
    db.put(&mut wtxn, "license", "OpenLDAP")?;

    wtxn.commit()?;

    // 3. Read — retrieve individual keys in a read transaction
    let rtxn = env.read_txn()?;

    match db.get(&rtxn, "name")? {
        Some(value) => println!("name = {}", value),
        None => println!("name = not found"),
    }
    match db.get(&rtxn, "type")? {
        Some(value) => println!("type = {}", value),
        None => println!("type = not found"),
    }

    rtxn.commit()?;

    // 4. Delete — remove a key in a write transaction
    let mut wtxn = env.write_txn()?;
    // Note: heed does not have a direct delete method; use del
    db.delete(&mut wtxn, "license")?;
    wtxn.commit()?;

    let rtxn = env.read_txn()?;
    match db.get(&rtxn, "license")? {
        Some(value) => println!("license after delete = {}", value),
        None => println!("license after delete = None"),
    }
    rtxn.commit()?;

    // 5. Scan — iterate over all entries
    println!("\nAll entries:");
    let rtxn = env.read_txn()?;
    let iter = db.iter(&rtxn)?;
    for result in iter {
        let (key, value) = result?;
        println!("  {} => {}", key, value);
    }
    // rtxn dropped at end of scope

    println!("\nDone.");
    Ok(())
}
