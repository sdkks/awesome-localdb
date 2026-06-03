use sanakirja::*;

const ROOT_DB: usize = 0;

fn setup_env() -> (tempfile::TempDir, Env) {
    let dir = tempfile::tempdir().unwrap();
    let path = dir.path().join("test.db");
    let env = Env::new(&path, 1 << 20, 2).unwrap();
    (dir, env)
}

/// Helper: get exact match from the default B-tree type (Db<u64, u64>).
/// `btree::get` returns the entry with key >= the search key (B-tree seek
/// semantics), so we must compare the returned key for exact-match semantics.
fn get_exact(txn: &Txn<&Env>, db: &btree::Db<u64, u64>, key: &u64) -> Option<u64> {
    btree::get(txn, db, key, None).unwrap().and_then(|(k, v)| if *k == *key { Some(*v) } else { None })
}

#[test]
fn test_basic_insert_and_get() {
    let (_dir, env) = setup_env();

    let mut txn = Env::mut_txn_begin(&env).unwrap();
    let mut db: btree::Db<u64, u64> = unsafe { btree::create_db::<_, u64, u64>(&mut txn).unwrap() };
    btree::put(&mut txn, &mut db, &42, &99).unwrap();
    txn.set_root(ROOT_DB, db.db.into());
    txn.commit().unwrap();

    let txn = Env::txn_begin(&env).unwrap();
    let db: btree::Db<u64, u64> = txn.root_db(ROOT_DB).unwrap();
    let result = btree::get(&txn, &db, &42, None).unwrap();
    assert!(result.is_some());
    let (k, v) = result.unwrap();
    assert_eq!(*k, 42);
    assert_eq!(*v, 99);
}

#[test]
fn test_delete_key() {
    let (_dir, env) = setup_env();

    let mut txn = Env::mut_txn_begin(&env).unwrap();
    let mut db: btree::Db<u64, u64> = unsafe { btree::create_db::<_, u64, u64>(&mut txn).unwrap() };
    btree::put(&mut txn, &mut db, &1, &10).unwrap();
    btree::put(&mut txn, &mut db, &2, &20).unwrap();
    txn.set_root(ROOT_DB, db.db.into());
    txn.commit().unwrap();

    // Verify both keys exist
    let txn = Env::txn_begin(&env).unwrap();
    let db: btree::Db<u64, u64> = txn.root_db(ROOT_DB).unwrap();
    assert!(get_exact(&txn, &db, &1).is_some());
    assert!(get_exact(&txn, &db, &2).is_some());
    drop(txn);

    // Delete key 1
    let mut txn = Env::mut_txn_begin(&env).unwrap();
    let mut db: btree::Db<u64, u64> = txn.root_db(ROOT_DB).unwrap();
    let deleted = btree::del(&mut txn, &mut db, &1, None).unwrap();
    assert!(deleted, "del should return true when key exists");
    txn.set_root(ROOT_DB, db.db.into());
    txn.commit().unwrap();

    let txn = Env::txn_begin(&env).unwrap();
    let db: btree::Db<u64, u64> = txn.root_db(ROOT_DB).unwrap();
    // Key 1 was deleted: get returns next entry (key 2), so exact match fails
    assert!(get_exact(&txn, &db, &1).is_none());
    assert!(get_exact(&txn, &db, &2).is_some());
}

#[test]
fn test_cursor_iteration_ordered() {
    let (_dir, env) = setup_env();

    let mut txn = Env::mut_txn_begin(&env).unwrap();
    let mut db: btree::Db<u64, u64> = unsafe { btree::create_db::<_, u64, u64>(&mut txn).unwrap() };
    btree::put(&mut txn, &mut db, &30, &300).unwrap();
    btree::put(&mut txn, &mut db, &10, &100).unwrap();
    btree::put(&mut txn, &mut db, &20, &200).unwrap();
    txn.set_root(ROOT_DB, db.db.into());
    txn.commit().unwrap();

    let txn = Env::txn_begin(&env).unwrap();
    let db: btree::Db<u64, u64> = txn.root_db(ROOT_DB).unwrap();
    let results: Vec<(u64, u64)> = btree::iter(&txn, &db, None)
        .unwrap()
        .map(|entry| {
            let (k, v) = entry.unwrap();
            (*k, *v)
        })
        .collect();

    assert_eq!(results.len(), 3);
    // B-tree iteration returns keys in sorted order
    assert_eq!(results[0], (10, 100));
    assert_eq!(results[1], (20, 200));
    assert_eq!(results[2], (30, 300));
}

#[test]
fn test_multiple_puts_and_gets() {
    let (_dir, env) = setup_env();

    let mut txn = Env::mut_txn_begin(&env).unwrap();
    let mut db: btree::Db<u64, u64> = unsafe { btree::create_db::<_, u64, u64>(&mut txn).unwrap() };
    let count = 100;
    for i in 0..count {
        btree::put(&mut txn, &mut db, &i, &(i * i)).unwrap();
    }
    txn.set_root(ROOT_DB, db.db.into());
    txn.commit().unwrap();

    let txn = Env::txn_begin(&env).unwrap();
    let db: btree::Db<u64, u64> = txn.root_db(ROOT_DB).unwrap();
    for i in 0..count {
        let val = get_exact(&txn, &db, &i);
        assert!(val.is_some(), "key {} should exist", i);
        assert_eq!(val.unwrap(), i * i);
    }
}

#[test]
fn test_concurrent_readers() {
    use std::sync::Arc;
    use std::thread;

    let dir = tempfile::tempdir().unwrap();
    let path = dir.path().join("concurrent.db");

    let env = Env::new(&path, 1 << 20, 4).unwrap();

    // Insert initial data
    let mut txn = Env::mut_txn_begin(&env).unwrap();
    let mut db: btree::Db<u64, u64> = unsafe { btree::create_db::<_, u64, u64>(&mut txn).unwrap() };
    btree::put(&mut txn, &mut db, &1, &999).unwrap();
    txn.set_root(ROOT_DB, db.db.into());
    txn.commit().unwrap();

    // Sanakirja's Env can be shared via Arc; txn_begin takes Borrow<Env>
    // which is implemented for Arc<Env> directly.
    let env = Arc::new(env);

    let mut handles = vec![];
    for _ in 0..4 {
        let env = Arc::clone(&env);
        let handle = thread::spawn(move || {
            let shared = env; // move Arc into closure
            let txn = Env::txn_begin(shared).unwrap();
            let db: btree::Db<u64, u64> = txn.root_db(ROOT_DB).unwrap();
            let result = btree::get(&txn, &db, &1, None).unwrap();
            result.filter(|(k, _)| **k == 1).map(|(_k, v)| *v)
        });
        handles.push(handle);
    }

    for handle in handles {
        let result = handle.join().unwrap();
        assert_eq!(result, Some(999));
    }
}

#[test]
fn test_drop_rollback() {
    // MutTxn that is dropped without commit acts as a rollback.
    let (_dir, env) = setup_env();

    // Insert version 1
    let mut txn = Env::mut_txn_begin(&env).unwrap();
    let mut db: btree::Db<u64, u64> = unsafe { btree::create_db::<_, u64, u64>(&mut txn).unwrap() };
    btree::put(&mut txn, &mut db, &1, &100).unwrap();
    txn.set_root(ROOT_DB, db.db.into());
    txn.commit().unwrap();

    // Start a mutable transaction, make changes, then drop (rollback)
    {
        let mut txn = Env::mut_txn_begin(&env).unwrap();
        let mut db: btree::Db<u64, u64> = txn.root_db(ROOT_DB).unwrap();
        btree::put(&mut txn, &mut db, &1, &200).unwrap();
        btree::put(&mut txn, &mut db, &2, &300).unwrap();
        // MutTxn dropped here without commit: changes are discarded
    }

    // Read back: only the committed data is visible
    let txn = Env::txn_begin(&env).unwrap();
    let db: btree::Db<u64, u64> = txn.root_db(ROOT_DB).unwrap();
    assert_eq!(get_exact(&txn, &db, &1), Some(100));
    assert_eq!(get_exact(&txn, &db, &2), None);
}
