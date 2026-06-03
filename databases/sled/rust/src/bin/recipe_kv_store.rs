//! Recipe: Basic KV Store Operations
//! Database: sled
//! Description: Demonstrates opening a database, inserting, getting, deleting
//!     keys, performing range scans, atomic compare-and-swap, merge operators,
//!     and watch subscriptions using the sled embedded database API.
//!
//! Usage: cargo run --bin recipe_kv_store

use sled;

fn main() -> sled::Result<()> {
    let dir = tempfile::tempdir()?;
    let db_path = dir.path().join("demo");

    // 1. Setup -- open or create the database
    let db = sled::open(&db_path)?;

    // 2. Write -- insert key-value pairs
    db.insert(b"name", b"sled")?;
    db.insert(b"type", b"key-value")?;
    db.insert(b"language", b"Rust")?;
    db.insert(b"license", b"Apache-2.0")?;

    // 3. Read -- retrieve individual keys
    match db.get(b"name")? {
        Some(val) => println!("name = {}", String::from_utf8_lossy(&val)),
        None => println!("name = not found"),
    }
    match db.get(b"type")? {
        Some(val) => println!("type = {}", String::from_utf8_lossy(&val)),
        None => println!("type = not found"),
    }

    // 4. Delete -- remove a key
    db.remove(b"license")?;

    match db.get(b"license")? {
        Some(val) => println!("license after delete = {}", String::from_utf8_lossy(&val)),
        None => println!("license after delete = None"),
    }

    // 5. Range scan -- iterate over entries in a key range
    db.insert(b"user:001:name", b"Alice")?;
    db.insert(b"user:001:email", b"alice@example.com")?;
    db.insert(b"user:002:name", b"Bob")?;
    db.insert(b"user:002:email", b"bob@example.com")?;

    println!("\nAll entries for user:001:");
    let start: &[u8] = b"user:001:";
    let end: &[u8] = b"user:001;";
    for kv in db.range(start..end) {
        let (key, val) = kv?;
        println!(
            "  {} => {}",
            String::from_utf8_lossy(&key),
            String::from_utf8_lossy(&val)
        );
    }

    // 6. Atomic compare-and-swap
    println!("\nCompare-and-swap operation:");
    let result = db.compare_and_swap(
        b"name",
        Some(b"sled"),    // expected current value
        Some(b"sled-cas"), // new value
    )?;
    match result {
        Ok(()) => println!("  CAS succeeded: name updated to sled-cas"),
        Err(sled::CompareAndSwapError { current, proposed: _ }) => println!(
            "  CAS failed: current value is {:?}",
            current.map(|v| String::from_utf8_lossy(&v).to_string())
        ),
    }

    // Verify the CAS result
    if let Some(val) = db.get(b"name")? {
        println!("  name after CAS = {}", String::from_utf8_lossy(&val));
    }

    // 7. Merge operator -- atomic read-modify-write
    println!("\nMerge operator:");
    db.set_merge_operator(concat_merge);
    db.merge(b"merged", b"hello")?;
    db.merge(b"merged", b" world")?;
    if let Some(val) = db.get(b"merged")? {
        println!("  merged value = {}", String::from_utf8_lossy(&val));
    }

    // 8. Watch prefix -- subscribe to key changes
    let mut subscriber = db.watch_prefix(b"user:");
    db.insert(b"user:003:name", b"Charlie")?;
    db.insert(b"user:003:email", b"charlie@example.com")?;

    println!("\nWatch prefix events:");
    let mut event_count = 0;
    while event_count < 2 {
        match subscriber.next_timeout(std::time::Duration::from_millis(100)) {
            Ok(sled::Event::Insert { key, value: _ }) => {
                println!("  Insert: {}", String::from_utf8_lossy(&key));
                event_count += 1;
            }
            Ok(sled::Event::Remove { key }) => {
                println!("  Remove: {}", String::from_utf8_lossy(&key));
                event_count += 1;
            }
            Err(_) => break, // timeout, no more events
        }
    }

    // 9. Durability -- flush to disk
    db.flush()?;
    println!("\nFlushed to disk. Database path: {:?}", db_path);
    println!("Done.");

    Ok(())
}

/// A merge operator that concatenates new values onto existing values,
/// separated by a newline.
fn concat_merge(
    _key: &[u8],
    existing_value: Option<&[u8]>,
    merged_bytes: &[u8],
) -> Option<Vec<u8>> {
    match existing_value {
        Some(old) => {
            let mut new = old.to_vec();
            new.extend_from_slice(merged_bytes);
            Some(new)
        }
        None => Some(merged_bytes.to_vec()),
    }
}
