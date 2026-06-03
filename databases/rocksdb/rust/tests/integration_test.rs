use rocksdb::{DB, IteratorMode, Options, WriteBatch};

#[test]
fn test_kv_store_operations() {
    let db_path = "/tmp/rocksdb_test_kv_store_rs";
    {
        let db = DB::open_default(db_path).unwrap();

        db.put(b"test_key", b"test_value").unwrap();
        assert_eq!(db.get(b"test_key").unwrap(), Some(b"test_value".to_vec()));

        db.delete(b"test_key").unwrap();
        assert_eq!(db.get(b"test_key").unwrap(), None);
    }
    let _ = DB::destroy(&Options::default(), db_path);
}

#[test]
fn test_iterator_scan() {
    let db_path = "/tmp/rocksdb_test_iterator_rs";
    {
        let db = DB::open_default(db_path).unwrap();

        db.put(b"a", b"1").unwrap();
        db.put(b"b", b"2").unwrap();
        db.put(b"c", b"3").unwrap();

        let results: Vec<_> = db
            .iterator(IteratorMode::Start)
            .map(|item| {
                let (k, v) = item.unwrap();
                (k.to_vec(), v.to_vec())
            })
            .collect();

        assert_eq!(results.len(), 3);
        assert_eq!(results[0], (b"a".to_vec(), b"1".to_vec()));
        assert_eq!(results[1], (b"b".to_vec(), b"2".to_vec()));
        assert_eq!(results[2], (b"c".to_vec(), b"3".to_vec()));
    }
    let _ = DB::destroy(&Options::default(), db_path);
}

#[test]
fn test_write_batch_atomic() {
    let db_path = "/tmp/rocksdb_test_batch_rs";
    {
        let db = DB::open_default(db_path).unwrap();

        let mut batch = WriteBatch::default();
        batch.put(b"batch:1", b"v1");
        batch.put(b"batch:2", b"v2");
        batch.put(b"batch:3", b"v3");
        batch.delete(b"batch:2");
        db.write(batch).unwrap();

        assert_eq!(db.get(b"batch:1").unwrap(), Some(b"v1".to_vec()));
        assert_eq!(db.get(b"batch:2").unwrap(), None);
        assert_eq!(db.get(b"batch:3").unwrap(), Some(b"v3".to_vec()));
    }
    let _ = DB::destroy(&Options::default(), db_path);
}

#[test]
fn test_write_batch_large_count() {
    let db_path = "/tmp/rocksdb_test_batch_large_rs";
    {
        let db = DB::open_default(db_path).unwrap();

        let mut batch = WriteBatch::default();
        let count = 100;
        for i in 0..count {
            let key = format!("key:{:04}", i);
            let val = format!("val:{:04}", i);
            batch.put(key.as_bytes(), val.as_bytes());
        }
        db.write(batch).unwrap();

        for i in 0..count {
            let key = format!("key:{:04}", i);
            let expected = format!("val:{:04}", i);
            assert_eq!(
                db.get(key.as_bytes()).unwrap(),
                Some(expected.as_bytes().to_vec())
            );
        }
    }
    let _ = DB::destroy(&Options::default(), db_path);
}
