use heed::types::Str;
use heed::{Database, EnvOpenOptions};

#[test]
fn test_kv_store_operations() {
    let dir = tempfile::tempdir().unwrap();
    let env = unsafe { EnvOpenOptions::new().max_dbs(1).open(dir.path()).unwrap() };

    let mut wtxn = env.write_txn().unwrap();
    let db: Database<Str, Str> = env.create_database(&mut wtxn, None).unwrap();

    db.put(&mut wtxn, "test_key", "test_value").unwrap();
    wtxn.commit().unwrap();

    let rtxn = env.read_txn().unwrap();
    assert_eq!(db.get(&rtxn, "test_key").unwrap(), Some("test_value"));
    rtxn.commit().unwrap();

    let mut wtxn = env.write_txn().unwrap();
    db.delete(&mut wtxn, "test_key").unwrap();
    wtxn.commit().unwrap();

    let rtxn = env.read_txn().unwrap();
    assert_eq!(db.get(&rtxn, "test_key").unwrap(), None);
    rtxn.commit().unwrap();
}

#[test]
fn test_cursor_iteration() {
    let dir = tempfile::tempdir().unwrap();
    let env = unsafe { EnvOpenOptions::new().max_dbs(1).open(dir.path()).unwrap() };

    let mut wtxn = env.write_txn().unwrap();
    let db: Database<Str, Str> = env.create_database(&mut wtxn, None).unwrap();

    db.put(&mut wtxn, "c", "3").unwrap();
    db.put(&mut wtxn, "a", "1").unwrap();
    db.put(&mut wtxn, "b", "2").unwrap();
    wtxn.commit().unwrap();

    let rtxn = env.read_txn().unwrap();
    let results: Vec<_> = db
        .iter(&rtxn)
        .unwrap()
        .map(|item| {
            let (k, v) = item.unwrap();
            (k.to_string(), v.to_string())
        })
        .collect();
    rtxn.commit().unwrap();

    assert_eq!(results.len(), 3);
    // LMDB returns keys in lexicographic order
    assert_eq!(results[0], ("a".to_string(), "1".to_string()));
    assert_eq!(results[1], ("b".to_string(), "2".to_string()));
    assert_eq!(results[2], ("c".to_string(), "3".to_string()));
}

#[test]
fn test_multiple_puts_and_gets() {
    let dir = tempfile::tempdir().unwrap();
    let env = unsafe { EnvOpenOptions::new().max_dbs(1).open(dir.path()).unwrap() };

    let mut wtxn = env.write_txn().unwrap();
    let db: Database<Str, Str> = env.create_database(&mut wtxn, None).unwrap();

    let count = 50;
    for i in 0..count {
        let key = format!("key:{:04}", i);
        let val = format!("val:{:04}", i);
        db.put(&mut wtxn, &key, &val).unwrap();
    }
    wtxn.commit().unwrap();

    let rtxn = env.read_txn().unwrap();
    for i in 0..count {
        let key = format!("key:{:04}", i);
        let expected = format!("val:{:04}", i);
        assert_eq!(db.get(&rtxn, &key).unwrap(), Some(expected.as_str()));
    }
    rtxn.commit().unwrap();
}

#[test]
fn test_concurrent_readers() {
    use std::sync::Arc;
    use std::thread;

    let dir = tempfile::tempdir().unwrap();
    let env = unsafe { EnvOpenOptions::new().max_dbs(1).open(dir.path()).unwrap() };

    let mut wtxn = env.write_txn().unwrap();
    let db: Database<Str, Str> = env.create_database(&mut wtxn, None).unwrap();
    db.put(&mut wtxn, "shared", "initial").unwrap();
    wtxn.commit().unwrap();

    // Share the Env across threads via Arc
    let env = Arc::new(env);

    // Spawn 4 threads that all read concurrently
    let mut handles = vec![];
    for _ in 0..4 {
        let env = Arc::clone(&env);
        let handle = thread::spawn(move || {
            let rtxn = env.read_txn().unwrap();
            let db: Database<Str, Str> =
                env.open_database(&rtxn, None).unwrap().unwrap();
            let val = db.get(&rtxn, "shared").unwrap().map(|s| s.to_string());
            rtxn.commit().unwrap();
            val
        });
        handles.push(handle);
    }

    for handle in handles {
        let result = handle.join().unwrap();
        assert_eq!(result, Some("initial".to_string()));
    }
}
