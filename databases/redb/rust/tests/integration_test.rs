use redb::{Database, ReadableDatabase, ReadableTable, TableDefinition};

const TABLE: TableDefinition<&str, &str> = TableDefinition::new("test_kv");

#[test]
fn test_basic_insert_and_get() {
    let dir = tempfile::tempdir().unwrap();
    let db = Database::create(dir.path().join("test.redb")).unwrap();

    let write_txn = db.begin_write().unwrap();
    {
        let mut table = write_txn.open_table(TABLE).unwrap();
        table.insert("test_key", "test_value").unwrap();
    }
    write_txn.commit().unwrap();

    let read_txn = db.begin_read().unwrap();
    let table = read_txn.open_table(TABLE).unwrap();
    let entry = table.get("test_key").unwrap().unwrap();
    assert_eq!(entry.value(), "test_value");
}

#[test]
fn test_delete_key() {
    let dir = tempfile::tempdir().unwrap();
    let db = Database::create(dir.path().join("delete.redb")).unwrap();

    let write_txn = db.begin_write().unwrap();
    {
        let mut table = write_txn.open_table(TABLE).unwrap();
        table.insert("tmp", "value").unwrap();
    }
    write_txn.commit().unwrap();

    let write_txn = db.begin_write().unwrap();
    {
        let mut table = write_txn.open_table(TABLE).unwrap();
        table.remove("tmp").unwrap();
    }
    write_txn.commit().unwrap();

    let read_txn = db.begin_read().unwrap();
    let table = read_txn.open_table(TABLE).unwrap();
    assert!(table.get("tmp").unwrap().is_none());
}

#[test]
fn test_cursor_iteration_ordered() {
    let dir = tempfile::tempdir().unwrap();
    let db = Database::create(dir.path().join("ordered.redb")).unwrap();

    let write_txn = db.begin_write().unwrap();
    {
        let mut table = write_txn.open_table(TABLE).unwrap();
        table.insert("c", "3").unwrap();
        table.insert("a", "1").unwrap();
        table.insert("b", "2").unwrap();
    }
    write_txn.commit().unwrap();

    let read_txn = db.begin_read().unwrap();
    let table = read_txn.open_table(TABLE).unwrap();
    let results: Vec<(String, String)> = table
        .iter()
        .unwrap()
        .map(|item| {
            let (k, v) = item.unwrap();
            (k.value().to_string(), v.value().to_string())
        })
        .collect();

    assert_eq!(results.len(), 3);
    // Keys are returned in lexicographic byte order
    assert_eq!(results[0], ("a".to_string(), "1".to_string()));
    assert_eq!(results[1], ("b".to_string(), "2".to_string()));
    assert_eq!(results[2], ("c".to_string(), "3".to_string()));
}

#[test]
fn test_multiple_puts_and_gets() {
    let dir = tempfile::tempdir().unwrap();
    let db = Database::create(dir.path().join("bulk.redb")).unwrap();

    let write_txn = db.begin_write().unwrap();
    let count = 50;
    {
        let mut table = write_txn.open_table(TABLE).unwrap();
        for i in 0..count {
            let key = format!("key:{:04}", i);
            let val = format!("val:{:04}", i);
            // We need to use owned strings, so let's leak them into &'static str
            // or use a different approach. Actually, redb's Table works with
            // references for &str keys/values since they implement Key/Value.
            table.insert(key.as_str(), val.as_str()).unwrap();
        }
    }
    write_txn.commit().unwrap();

    let read_txn = db.begin_read().unwrap();
    let table = read_txn.open_table(TABLE).unwrap();
    for i in 0..count {
        let key = format!("key:{:04}", i);
        let expected = format!("val:{:04}", i);
        let entry = table.get(key.as_str()).unwrap().unwrap();
        assert_eq!(entry.value(), expected.as_str());
    }
}

#[test]
fn test_concurrent_readers() {
    use std::sync::Arc;
    use std::thread;

    let dir = tempfile::tempdir().unwrap();
    let db_path = dir.path().join("concurrent.redb");
    let db = Database::create(&db_path).unwrap();

    let write_txn = db.begin_write().unwrap();
    {
        let mut table = write_txn.open_table(TABLE).unwrap();
        table.insert("shared", "initial").unwrap();
    }
    write_txn.commit().unwrap();

    let db = Arc::new(db);

    let mut handles = vec![];
    for _ in 0..4 {
        let db = Arc::clone(&db);
        let handle = thread::spawn(move || {
            let read_txn = db.begin_read().unwrap();
            let table = read_txn.open_table(TABLE).unwrap();
            let val = table.get("shared").unwrap().map(|e| e.value().to_string());
            val
        });
        handles.push(handle);
    }

    for handle in handles {
        let result = handle.join().unwrap();
        assert_eq!(result, Some("initial".to_string()));
    }
}

#[test]
fn test_typed_table_with_integers() {
    const INT_TABLE: TableDefinition<u64, u64> = TableDefinition::new("int_kv");

    let dir = tempfile::tempdir().unwrap();
    let db = Database::create(dir.path().join("ints.redb")).unwrap();

    let write_txn = db.begin_write().unwrap();
    {
        let mut table = write_txn.open_table(INT_TABLE).unwrap();
        table.insert(1, 100).unwrap();
        table.insert(2, 200).unwrap();
        table.insert(3, 300).unwrap();
    }
    write_txn.commit().unwrap();

    let read_txn = db.begin_read().unwrap();
    let table = read_txn.open_table(INT_TABLE).unwrap();

    assert_eq!(table.get(2).unwrap().unwrap().value(), 200);

    // Range query
    let range = table.range(1..3).unwrap();
    let results: Vec<(u64, u64)> = range
        .map(|item| {
            let (k, v) = item.unwrap();
            (k.value(), v.value())
        })
        .collect();
    assert_eq!(results, vec![(1, 100), (2, 200)]);
}

#[test]
fn test_drop_rollback() {
    let dir = tempfile::tempdir().unwrap();
    let db = Database::create(dir.path().join("droprollback.redb")).unwrap();

    // Insert initial data, then rollback by dropping without commit
    let write_txn = db.begin_write().unwrap();
    {
        let mut table = write_txn.open_table(TABLE).unwrap();
        table.insert("version", "1").unwrap();
    }
    write_txn.commit().unwrap();

    // Start a write transaction, insert, then rollback via savepoint
    let write_txn = db.begin_write().unwrap();
    {
        let mut table = write_txn.open_table(TABLE).unwrap();
        table.insert("version", "2").unwrap();
        table.insert("extra", "should-not-persist").unwrap();
    }

    // We don't commit -- just drop the write_txn, which acts as a rollback
    drop(write_txn);

    // Verify that "version" is still "1" and "extra" does not exist
    let read_txn = db.begin_read().unwrap();
    let table = read_txn.open_table(TABLE).unwrap();
    assert_eq!(table.get("version").unwrap().unwrap().value(), "1");
    assert!(table.get("extra").unwrap().is_none());
}
