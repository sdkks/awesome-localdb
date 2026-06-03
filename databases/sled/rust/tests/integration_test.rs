use sled;

#[test]
fn test_basic_insert_and_get() {
    let dir = tempfile::tempdir().unwrap();
    let db = sled::open(dir.path().join("test")).unwrap();

    db.insert(b"test_key", b"test_value").unwrap();

    let result = db.get(b"test_key").unwrap().unwrap();
    assert_eq!(&result[..], b"test_value");
}

#[test]
fn test_delete_key() {
    let dir = tempfile::tempdir().unwrap();
    let db = sled::open(dir.path().join("delete")).unwrap();

    db.insert(b"tmp", b"value").unwrap();
    db.remove(b"tmp").unwrap();

    assert!(db.get(b"tmp").unwrap().is_none());
}

#[test]
fn test_range_scan() {
    let dir = tempfile::tempdir().unwrap();
    let db = sled::open(dir.path().join("range")).unwrap();

    db.insert(b"user:1:name", b"Alice").unwrap();
    db.insert(b"user:1:email", b"alice@example.com").unwrap();
    db.insert(b"user:2:name", b"Bob").unwrap();

    let start: &[u8] = b"user:1:";
    let end: &[u8] = b"user:1;";
    let mut results: Vec<(String, String)> = Vec::new();
    for kv in db.range(start..end) {
        let (key, val) = kv.unwrap();
        results.push((
            String::from_utf8_lossy(&key).to_string(),
            String::from_utf8_lossy(&val).to_string(),
        ));
    }

    assert_eq!(results.len(), 2);
    assert!(results
        .iter()
        .any(|(k, v)| k == "user:1:name" && v == "Alice"));
    assert!(results
        .iter()
        .any(|(k, v)| k == "user:1:email" && v == "alice@example.com"));
}

#[test]
fn test_compare_and_swap_success() {
    let dir = tempfile::tempdir().unwrap();
    let db = sled::open(dir.path().join("cas")).unwrap();

    db.insert(b"key", b"old").unwrap();

    let result = db
        .compare_and_swap(b"key", Some(b"old"), Some(b"new"))
        .unwrap();
    assert!(result.is_ok());

    assert_eq!(&db.get(b"key").unwrap().unwrap()[..], b"new");
}

#[test]
fn test_compare_and_swap_failure() {
    let dir = tempfile::tempdir().unwrap();
    let db = sled::open(dir.path().join("cas_fail")).unwrap();

    db.insert(b"key", b"unexpected").unwrap();

    let result = db
        .compare_and_swap(b"key", Some(b"expected"), Some(b"new"))
        .unwrap();
    assert!(result.is_err());

    // Value should be unchanged
    assert_eq!(&db.get(b"key").unwrap().unwrap()[..], b"unexpected");
}

#[test]
fn test_multiple_trees() {
    let dir = tempfile::tempdir().unwrap();
    let db = sled::open(dir.path().join("multi")).unwrap();

    let users = db.open_tree(b"users").unwrap();
    let posts = db.open_tree(b"posts").unwrap();

    users.insert(b"u:1", b"Alice").unwrap();
    users.insert(b"u:2", b"Bob").unwrap();
    posts.insert(b"p:1", b"Hello").unwrap();
    posts.insert(b"p:2", b"World").unwrap();

    assert_eq!(&users.get(b"u:1").unwrap().unwrap()[..], b"Alice");
    assert_eq!(&posts.get(b"p:2").unwrap().unwrap()[..], b"World");

    // Verify isolation: posts should not have user keys
    assert!(posts.get(b"u:1").unwrap().is_none());
    assert!(users.get(b"p:1").unwrap().is_none());
}

#[test]
fn test_flush_durability() {
    let dir = tempfile::tempdir().unwrap();
    let db_path = dir.path().join("persist");

    {
        let db = sled::open(&db_path).unwrap();
        db.insert(b"durable", b"yes").unwrap();
        db.flush().unwrap();
    }

    // Reopen and verify data survived
    let db = sled::open(&db_path).unwrap();
    assert_eq!(&db.get(b"durable").unwrap().unwrap()[..], b"yes");
}

#[test]
fn test_concurrent_readers() {
    use std::sync::Arc;
    use std::thread;

    let dir = tempfile::tempdir().unwrap();
    let db = sled::open(dir.path().join("concurrent")).unwrap();

    db.insert(b"key", b"value").unwrap();
    db.flush().unwrap();

    let db = Arc::new(db);

    let mut handles = vec![];
    for _ in 0..4 {
        let db = Arc::clone(&db);
        let handle = thread::spawn(move || {
            let val = db.get(b"key").unwrap().map(|v| v.to_vec());
            val
        });
        handles.push(handle);
    }

    for handle in handles {
        let result = handle.join().unwrap();
        assert_eq!(result, Some(b"value".to_vec()));
    }
}

#[test]
fn test_merge_operator() {
    let dir = tempfile::tempdir().unwrap();
    let db = sled::open(dir.path().join("merge")).unwrap();

    fn append_merge(
        _key: &[u8],
        existing: Option<&[u8]>,
        merged: &[u8],
    ) -> Option<Vec<u8>> {
        match existing {
            Some(old) => {
                let mut new = old.to_vec();
                new.extend_from_slice(merged);
                Some(new)
            }
            None => Some(merged.to_vec()),
        }
    }

    db.set_merge_operator(append_merge);

    db.merge(b"accum", b"a").unwrap();
    db.merge(b"accum", b"b").unwrap();
    db.merge(b"accum", b"c").unwrap();

    let result = db.get(b"accum").unwrap().unwrap();
    assert_eq!(&result[..], b"abc");
}

#[test]
fn test_bulk_insert_and_scan() {
    let dir = tempfile::tempdir().unwrap();
    let db = sled::open(dir.path().join("bulk")).unwrap();

    let count = 100;
    for i in 0..count {
        let key = format!("key:{:04}", i);
        let val = format!("val:{:04}", i);
        db.insert(key.as_bytes(), val.as_bytes()).unwrap();
    }

    let start: &[u8] = b"key:";
    let end: &[u8] = b"key;";
    let mut count_found = 0;
    for _ in db.range(start..end) {
        count_found += 1;
    }

    assert_eq!(count_found, count);

    // Verify specific keys exist
    let key0 = format!("key:{:04}", 0);
    let val0 = format!("val:{:04}", 0);
    assert_eq!(
        &db.get(key0.as_bytes()).unwrap().unwrap()[..],
        val0.as_bytes()
    );
}

#[test]
fn test_watch_prefix() {
    let dir = tempfile::tempdir().unwrap();
    let db = sled::open(dir.path().join("watch")).unwrap();

    let mut subscriber = db.watch_prefix(b"events:");

    db.insert(b"events:1", b"first").unwrap();
    db.insert(b"events:2", b"second").unwrap();

    let mut events = Vec::new();
    // Read available events with a short timeout
    let timeout = std::time::Duration::from_millis(100);
    loop {
        match subscriber.next_timeout(timeout) {
            Ok(sled::Event::Insert { key, value: _ }) => {
                events.push(String::from_utf8_lossy(&key).to_string());
            }
            Ok(_) => {}
            Err(_) => break, // timeout
        }
    }

    assert!(events.len() >= 1);
    assert!(events.iter().any(|e| e == "events:1"));
}

#[test]
fn test_transaction() {
    let dir = tempfile::tempdir().unwrap();
    let db = sled::open(dir.path().join("txn")).unwrap();

    // Perform multiple writes atomically
    db.transaction(|tx_db| -> sled::transaction::ConflictableTransactionResult<()> {
        tx_db.insert(b"a", b"1")?;
        tx_db.insert(b"b", b"2")?;
        tx_db.insert(b"c", b"3")?;
        Ok(())
    })
    .unwrap();

    assert_eq!(&db.get(b"a").unwrap().unwrap()[..], b"1");
    assert_eq!(&db.get(b"b").unwrap().unwrap()[..], b"2");
    assert_eq!(&db.get(b"c").unwrap().unwrap()[..], b"3");
}

#[test]
fn test_transaction_rollback() {
    let dir = tempfile::tempdir().unwrap();
    let db = sled::open(dir.path().join("txn_rollback")).unwrap();

    db.insert(b"existing", b"value").unwrap();

    // Transaction that fails mid-way using ConflictableTransactionError::Abort
    let result = db.transaction(|tx_db| {
        tx_db.insert(b"new_key", b"new_val")?;
        // Simulate an error condition by aborting the transaction
        if tx_db.get(b"existing")?.is_some() {
            return Err(sled::transaction::ConflictableTransactionError::Abort(
                "simulated rollback",
            ));
        }
        Ok(())
    });

    // The transaction should have been aborted (returned Err(Abort))
    assert!(result.is_err());

    // new_key should NOT have been inserted (rollback)
    assert!(db.get(b"new_key").unwrap().is_none());
    // existing key should still be there
    assert_eq!(&db.get(b"existing").unwrap().unwrap()[..], b"value");
}
