//! Recipe: Basic KV Store Operations
//! Database: Sanakirja
//! Description: Demonstrates creating an environment, opening a B-tree database,
//!     inserting, getting, deleting keys, and iterating entries using the Sanakirja
//!     transactional API with root page management. Note: `btree::get` returns the
//!     first entry with key >= the search key; always compare the returned key for
//!     exact-match semantics.
//!
//! Usage: cargo run --bin recipe_kv_store

use sanakirja::*;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let dir = tempfile::tempdir()?;
    let db_path = dir.path().join("demo.db");

    // 1. Setup — create the environment with 1 MiB initial size and 2 versions
    let env = Env::new(&db_path, 1 << 20, 2)?;

    // 2. Write — insert key-value pairs in a mutable transaction
    let mut txn = Env::mut_txn_begin(&env)?;
    let mut db: btree::Db<u64, u64> = unsafe { btree::create_db::<_, u64, u64>(&mut txn)? };

    btree::put(&mut txn, &mut db, &1, &100)?;
    btree::put(&mut txn, &mut db, &2, &200)?;
    btree::put(&mut txn, &mut db, &3, &300)?;

    // Store the database root pointer so we can retrieve it later
    const ROOT_DB: usize = 0;
    txn.set_root(ROOT_DB, db.db.into());
    txn.commit()?;

    // 3. Read — retrieve individual keys in a read transaction.
    //    IMPORTANT: btree::get returns the first entry with key >= the search key
    //    (B-tree seek semantics). Compare the returned key for exact-match logic.
    let txn = Env::txn_begin(&env)?;
    let db: btree::Db<u64, u64> = txn.root_db(ROOT_DB).ok_or("root_db not found")?;

    for key in [1, 2, 3] {
        let result = btree::get(&txn, &db, &key, None)?;
        match result {
            Some((k, v)) if *k == key => println!("key {} = {}", k, v),
            _ => println!("key {} = not found", key),
        }
    }

    // 4. Delete — remove a key in a mutable transaction
    let mut txn = Env::mut_txn_begin(&env)?;
    let mut db: btree::Db<u64, u64> = txn.root_db(ROOT_DB).ok_or("root_db not found")?;
    btree::del(&mut txn, &mut db, &2, None)?;
    txn.set_root(ROOT_DB, db.db.into());
    txn.commit()?;

    let txn = Env::txn_begin(&env)?;
    let db: btree::Db<u64, u64> = txn.root_db(ROOT_DB).ok_or("root_db not found")?;
    let result = btree::get(&txn, &db, &2, None)?;
    match result {
        Some((k, v)) if *k == 2 => println!("key 2 after delete = {}", v),
        _ => println!("key 2 after delete = None"),
    }

    // 5. Scan — iterate over all entries
    println!("\nAll entries:");
    let txn = Env::txn_begin(&env)?;
    let db: btree::Db<u64, u64> = txn.root_db(ROOT_DB).ok_or("root_db not found")?;
    for entry in btree::iter(&txn, &db, None)? {
        let (k, v) = entry?;
        println!("  {} => {}", k, v);
    }

    println!("\nDone.");
    Ok(())
}
