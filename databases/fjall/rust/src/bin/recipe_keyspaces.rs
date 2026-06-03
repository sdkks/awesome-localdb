//! Recipe: Multiple Keyspaces with Cross-Keyspace Operations
//! Database: fjall
//! Description: Demonstrates using multiple keyspaces for isolating data
//!     domains, including cross-keyspace atomic writes via write batches
//!     and single-writer transactions.
//!
//! Usage: cargo run --bin recipe_keyspaces

use fjall::{
    Database, KeyspaceCreateOptions, OwnedWriteBatch, PersistMode, SingleWriterTxDatabase,
};

fn main() -> fjall::Result<()> {
    let dir = tempfile::tempdir()?;
    let db_path = dir.path().join("keyspaces");

    // 1. Setup -- create database with multiple keyspaces
    let db = Database::builder(&db_path).open()?;
    let users = db.keyspace("users", || KeyspaceCreateOptions::default())?;
    let posts = db.keyspace("posts", || KeyspaceCreateOptions::default())?;

    // 2. Write to separate keyspaces
    users.insert("u:1", b"Alice")?;
    users.insert("u:2", b"Bob")?;
    users.insert("u:3", b"Carol")?;

    posts.insert("p:1", b"Hello, world!")?;
    posts.insert("p:2", b"Fjall is great")?;
    posts.insert("p:3", b"LSM-trees rock")?;

    // 3. Read from each keyspace independently
    println!("Users:");
    for guard in users.prefix("u:") {
        let (key, value) = guard.into_inner()?;
        println!(
            "  {} => {}",
            String::from_utf8_lossy(&key),
            String::from_utf8_lossy(&value)
        );
    }

    println!("\nPosts:");
    for guard in posts.prefix("p:") {
        let (key, value) = guard.into_inner()?;
        println!(
            "  {} => {}",
            String::from_utf8_lossy(&key),
            String::from_utf8_lossy(&value)
        );
    }

    // 4. Atomic write batch -- cross-keyspace atomicity
    println!("\nExecuting atomic write batch...");
    let mut batch = OwnedWriteBatch::with_capacity(db.clone(), 3);
    batch.insert(&users, "u:4", b"Dave");
    batch.insert(&posts, "p:4", b"Another post");
    // This delete is part of the same atomic batch
    batch.remove(&posts, "p:2");
    batch.commit()?;

    println!("After batch:");
    println!("  Users:");
    for guard in users.prefix("u:") {
        let (key, value) = guard.into_inner()?;
        println!(
            "    {} => {}",
            String::from_utf8_lossy(&key),
            String::from_utf8_lossy(&value)
        );
    }
    println!("  Posts:");
    for guard in posts.prefix("p:") {
        let (key, value) = guard.into_inner()?;
        println!(
            "    {} => {}",
            String::from_utf8_lossy(&key),
            String::from_utf8_lossy(&value)
        );
    }

    // 5. Transactions -- serializable cross-keyspace writes
    println!("\nTransactional database example:");
    let tx_db = SingleWriterTxDatabase::builder(&db_path.join("tx")).open()?;
    let tx_users = tx_db.keyspace("users", || KeyspaceCreateOptions::default())?;
    let tx_scores = tx_db.keyspace("scores", || KeyspaceCreateOptions::default())?;

    // Pre-populate
    tx_users.insert("alice", b"Alice")?;
    tx_scores.insert("alice", b"100")?;

    // Atomic transaction: update user and score together
    let mut tx = tx_db.write_tx();
    tx.insert(&tx_users, "alice", b"Alice (updated)");
    tx.insert(&tx_scores, "alice", b"200");
    tx.commit()?;

    println!("After transaction:");
    if let Some(name) = tx_users.get("alice")? {
        println!("  alice name = {}", String::from_utf8_lossy(&name));
    }
    if let Some(score) = tx_scores.get("alice")? {
        println!("  alice score = {}", String::from_utf8_lossy(&score));
    }

    db.persist(PersistMode::SyncAll)?;
    println!("\nDone.");
    Ok(())
}
