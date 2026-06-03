use fjall::{Database, KeyspaceCreateOptions, OwnedWriteBatch, PersistMode};

#[test]
fn test_basic_insert_and_get() {
    let dir = tempfile::tempdir().unwrap();
    let db = Database::builder(dir.path().join("test")).open().unwrap();
    let items = db
        .keyspace("kv", || KeyspaceCreateOptions::default())
        .unwrap();

    items.insert("test_key", b"test_value").unwrap();

    let result = items.get("test_key").unwrap().unwrap();
    assert_eq!(&result[..], b"test_value");
}

#[test]
fn test_delete_key() {
    let dir = tempfile::tempdir().unwrap();
    let db = Database::builder(dir.path().join("delete")).open().unwrap();
    let items = db
        .keyspace("kv", || KeyspaceCreateOptions::default())
        .unwrap();

    items.insert("tmp", b"value").unwrap();
    items.remove("tmp").unwrap();

    assert!(items.get("tmp").unwrap().is_none());
}

#[test]
fn test_prefix_scan() {
    let dir = tempfile::tempdir().unwrap();
    let db = Database::builder(dir.path().join("prefix")).open().unwrap();
    let items = db
        .keyspace("prefixed", || KeyspaceCreateOptions::default())
        .unwrap();

    items.insert("user:1:name", b"Alice").unwrap();
    items.insert("user:1:email", b"alice@example.com").unwrap();
    items.insert("user:2:name", b"Bob").unwrap();

    let mut results: Vec<(String, String)> = Vec::new();
    for guard in items.prefix("user:1") {
        let (key, value) = guard.into_inner().unwrap();
        results.push((
            String::from_utf8_lossy(&key).to_string(),
            String::from_utf8_lossy(&value).to_string(),
        ));
    }

    assert_eq!(results.len(), 2);
    assert!(results.iter().any(|(k, v)| k == "user:1:name" && v == "Alice"));
    assert!(results
        .iter()
        .any(|(k, v)| k == "user:1:email" && v == "alice@example.com"));
}

#[test]
fn test_range_iteration() {
    let dir = tempfile::tempdir().unwrap();
    let db = Database::builder(dir.path().join("range")).open().unwrap();
    let items = db
        .keyspace("range_items", || KeyspaceCreateOptions::default())
        .unwrap();

    items.insert("a", b"1").unwrap();
    items.insert("b", b"2").unwrap();
    items.insert("c", b"3").unwrap();
    items.insert("d", b"4").unwrap();

    let mut results: Vec<(String, String)> = Vec::new();
    for guard in items.range("a"..="c") {
        let (key, value) = guard.into_inner().unwrap();
        results.push((
            String::from_utf8_lossy(&key).to_string(),
            String::from_utf8_lossy(&value).to_string(),
        ));
    }

    assert_eq!(results.len(), 3);
    assert_eq!(results[0], ("a".to_string(), "1".to_string()));
    assert_eq!(results[1], ("b".to_string(), "2".to_string()));
    assert_eq!(results[2], ("c".to_string(), "3".to_string()));
}

#[test]
fn test_multiple_keyspaces() {
    let dir = tempfile::tempdir().unwrap();
    let db = Database::builder(dir.path().join("multi")).open().unwrap();

    let users = db
        .keyspace("users", || KeyspaceCreateOptions::default())
        .unwrap();
    let posts = db
        .keyspace("posts", || KeyspaceCreateOptions::default())
        .unwrap();

    users.insert("u:1", b"Alice").unwrap();
    users.insert("u:2", b"Bob").unwrap();
    posts.insert("p:1", b"Hello").unwrap();
    posts.insert("p:2", b"World").unwrap();

    assert_eq!(&users.get("u:1").unwrap().unwrap()[..], b"Alice");
    assert_eq!(&posts.get("p:2").unwrap().unwrap()[..], b"World");

    // Verify isolation: posts should not have user keys
    assert!(posts.get("u:1").unwrap().is_none());
    assert!(users.get("p:1").unwrap().is_none());
}

#[test]
fn test_write_batch_cross_keyspace() {
    let dir = tempfile::tempdir().unwrap();
    let db = Database::builder(dir.path().join("batch")).open().unwrap();

    let k1 = db
        .keyspace("one", || KeyspaceCreateOptions::default())
        .unwrap();
    let k2 = db
        .keyspace("two", || KeyspaceCreateOptions::default())
        .unwrap();

    let mut batch = OwnedWriteBatch::with_capacity(db.clone(), 3);
    batch.insert(&k1, "a", b"1");
    batch.insert(&k2, "b", b"2");
    batch.remove(&k1, "a"); // delete what we just inserted
    batch.commit().unwrap();

    // k1 "a" should be deleted
    assert!(k1.get("a").unwrap().is_none());
    // k2 "b" should still exist
    assert_eq!(&k2.get("b").unwrap().unwrap()[..], b"2");
}

#[test]
fn test_persist_durability() {
    let dir = tempfile::tempdir().unwrap();
    let db_path = dir.path().join("persist");

    {
        let db = Database::builder(&db_path).open().unwrap();
        let items = db
            .keyspace("kv", || KeyspaceCreateOptions::default())
            .unwrap();
        items.insert("durable", b"yes").unwrap();
        db.persist(PersistMode::SyncAll).unwrap();
    }

    // Reopen and verify data survived
    let db = Database::builder(&db_path).open().unwrap();
    let items = db
        .keyspace("kv", || KeyspaceCreateOptions::default())
        .unwrap();
    assert_eq!(
        &items.get("durable").unwrap().unwrap()[..],
        b"yes"
    );
}

#[test]
fn test_concurrent_readers() {
    use std::sync::Arc;
    use std::thread;

    let dir = tempfile::tempdir().unwrap();
    let db_path = dir.path().join("concurrent");
    let db = Database::builder(&db_path).open().unwrap();
    let items = db
        .keyspace("shared", || KeyspaceCreateOptions::default())
        .unwrap();

    items.insert("key", b"value").unwrap();
    db.persist(PersistMode::SyncAll).unwrap();

    let items = Arc::new(items);

    let mut handles = vec![];
    for _ in 0..4 {
        let items = Arc::clone(&items);
        let handle = thread::spawn(move || {
            let val = items.get("key").unwrap().map(|v| v.to_vec());
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
fn test_bulk_insert_and_scan() {
    let dir = tempfile::tempdir().unwrap();
    let db = Database::builder(dir.path().join("bulk")).open().unwrap();
    let items = db
        .keyspace("bulk_kv", || KeyspaceCreateOptions::default())
        .unwrap();

    let count = 100;
    for i in 0..count {
        let key = format!("key:{:04}", i);
        let val = format!("val:{:04}", i);
        items.insert(key.as_bytes(), val.as_bytes()).unwrap();
    }

    let mut count_found = 0;
    for _ in items.prefix("key:") {
        count_found += 1;
    }

    assert_eq!(count_found, count);

    // Verify specific keys exist
    let key0 = format!("key:{:04}", 0);
    let val0 = format!("val:{:04}", 0);
    assert_eq!(
        &items.get(key0.as_bytes()).unwrap().unwrap()[..],
        val0.as_bytes()
    );
}
