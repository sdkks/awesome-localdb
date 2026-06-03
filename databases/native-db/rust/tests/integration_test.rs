use native_db::*;
use native_model::{native_model, Model};
use once_cell::sync::Lazy;
use serde::{Deserialize, Serialize};

// ─── Models ─────────────────────────────────────────────────────────────

#[derive(Serialize, Deserialize, PartialEq, Debug, Clone)]
#[native_model(id = 1, version = 1)]
#[native_db]
struct Item {
    #[primary_key]
    id: u32,
    #[secondary_key]
    name: String,
}

static MODELS: Lazy<Models> = Lazy::new(|| {
    let mut models = Models::new();
    models.define::<Item>().unwrap();
    models
});

fn open_db() -> Database<'static> {
    Builder::new().create_in_memory(&MODELS).unwrap()
}

// ─── Tests ──────────────────────────────────────────────────────────────

#[test]
fn test_insert_and_get_by_primary_key() {
    let db = open_db();

    let rw = db.rw_transaction().unwrap();
    rw.insert(Item {
        id: 1,
        name: "red".to_string(),
    })
    .unwrap();
    rw.insert(Item {
        id: 2,
        name: "green".to_string(),
    })
    .unwrap();
    rw.commit().unwrap();

    let r = db.r_transaction().unwrap();
    let item: Item = r.get().primary(1_u32).unwrap().unwrap();
    assert_eq!(item.id, 1);
    assert_eq!(item.name, "red");

    let item: Item = r.get().primary(2_u32).unwrap().unwrap();
    assert_eq!(item.name, "green");
}

#[test]
fn test_get_nonexistent_returns_none() {
    let db = open_db();

    let rw = db.rw_transaction().unwrap();
    rw.insert(Item {
        id: 1,
        name: "one".to_string(),
    })
    .unwrap();
    rw.commit().unwrap();

    let r = db.r_transaction().unwrap();
    let result: Option<Item> = r.get().primary(999_u32).unwrap();
    assert!(result.is_none());
}

#[test]
fn test_upsert_inserts_or_updates() {
    let db = open_db();

    // Insert via upsert
    let rw = db.rw_transaction().unwrap();
    rw.upsert(Item {
        id: 10,
        name: "original".to_string(),
    })
    .unwrap();
    rw.commit().unwrap();

    // Verify
    let r = db.r_transaction().unwrap();
    let item: Item = r.get().primary(10_u32).unwrap().unwrap();
    assert_eq!(item.name, "original");

    // Upsert with same primary key updates
    let rw = db.rw_transaction().unwrap();
    rw.upsert(Item {
        id: 10,
        name: "updated".to_string(),
    })
    .unwrap();
    rw.commit().unwrap();

    let r = db.r_transaction().unwrap();
    let item: Item = r.get().primary(10_u32).unwrap().unwrap();
    assert_eq!(item.name, "updated");
}

#[test]
fn test_update_replaces_existing() {
    let db = open_db();

    let rw = db.rw_transaction().unwrap();
    rw.insert(Item {
        id: 5,
        name: "old".to_string(),
    })
    .unwrap();
    rw.commit().unwrap();

    let rw = db.rw_transaction().unwrap();
    rw.update(
        Item {
            id: 5,
            name: "old".to_string(),
        },
        Item {
            id: 5,
            name: "new".to_string(),
        },
    )
    .unwrap();
    rw.commit().unwrap();

    let r = db.r_transaction().unwrap();
    let item: Item = r.get().primary(5_u32).unwrap().unwrap();
    assert_eq!(item.name, "new");
}

#[test]
fn test_remove_key() {
    let db = open_db();

    let rw = db.rw_transaction().unwrap();
    rw.insert(Item {
        id: 42,
        name: "temp".to_string(),
    })
    .unwrap();
    rw.commit().unwrap();

    // Verify it exists
    let r = db.r_transaction().unwrap();
    let item: Item = r.get().primary(42_u32).unwrap().unwrap();
    assert_eq!(item.name, "temp");
    drop(r);

    // Remove
    let rw = db.rw_transaction().unwrap();
    rw.remove(item).unwrap();
    rw.commit().unwrap();

    // Verify gone
    let r = db.r_transaction().unwrap();
    let result: Option<Item> = r.get().primary(42_u32).unwrap();
    assert!(result.is_none());
}

#[test]
fn test_scan_all_primary() {
    let db = open_db();

    let rw = db.rw_transaction().unwrap();
    for i in [3, 1, 2].iter() {
        rw.insert(Item {
            id: *i,
            name: format!("item-{}", i),
        })
        .unwrap();
    }
    rw.commit().unwrap();

    let r = db.r_transaction().unwrap();
    let items: Vec<Item> = r
        .scan()
        .primary::<Item>()
        .unwrap()
        .all()
        .unwrap()
        .collect::<Result<Vec<_>, _>>()
        .unwrap();
    assert_eq!(items.len(), 3);

    // Sorted by primary key
    let ids: Vec<u32> = items.iter().map(|i| i.id).collect();
    assert_eq!(ids, vec![1, 2, 3]);
}

#[test]
fn test_scan_secondary_start_with() {
    let db = open_db();

    let rw = db.rw_transaction().unwrap();
    rw.insert(Item {
        id: 1,
        name: "apple".to_string(),
    })
    .unwrap();
    rw.insert(Item {
        id: 2,
        name: "apricot".to_string(),
    })
    .unwrap();
    rw.insert(Item {
        id: 3,
        name: "banana".to_string(),
    })
    .unwrap();
    rw.commit().unwrap();

    let r = db.r_transaction().unwrap();
    let items: Vec<Item> = r
        .scan()
        .secondary::<Item>(ItemKey::name)
        .unwrap()
        .start_with("ap")
        .unwrap()
        .collect::<Result<Vec<_>, _>>()
        .unwrap();

    assert_eq!(items.len(), 2);
    let names: Vec<String> = items.iter().map(|i| i.name.clone()).collect();
    assert!(names.contains(&"apple".to_string()));
    assert!(names.contains(&"apricot".to_string()));
}

#[test]
fn test_scan_secondary_range() {
    let db = open_db();

    let rw = db.rw_transaction().unwrap();
    rw.insert(Item {
        id: 1,
        name: "alpha".to_string(),
    })
    .unwrap();
    rw.insert(Item {
        id: 2,
        name: "beta".to_string(),
    })
    .unwrap();
    rw.insert(Item {
        id: 3,
        name: "gamma".to_string(),
    })
    .unwrap();
    rw.insert(Item {
        id: 4,
        name: "delta".to_string(),
    })
    .unwrap();
    rw.commit().unwrap();

    let r = db.r_transaction().unwrap();
    let items: Vec<Item> = r
        .scan()
        .secondary::<Item>(ItemKey::name)
        .unwrap()
        .range("alpha".to_string()..="beta".to_string())
        .unwrap()
        .collect::<Result<Vec<_>, _>>()
        .unwrap();

    assert_eq!(items.len(), 2);
    let names: Vec<String> = items.iter().map(|i| i.name.clone()).collect();
    assert!(names.contains(&"alpha".to_string()));
    assert!(names.contains(&"beta".to_string()));
}

#[test]
fn test_len_by_primary() {
    let db = open_db();

    let rw = db.rw_transaction().unwrap();
    for i in 0..5 {
        rw.insert(Item {
            id: i,
            name: format!("n{}", i),
        })
        .unwrap();
    }
    rw.commit().unwrap();

    let r = db.r_transaction().unwrap();
    let count = r.len().primary::<Item>().unwrap();
    assert_eq!(count, 5);
}

#[test]
fn test_duplicate_primary_key_fails() {
    let db = open_db();

    let rw = db.rw_transaction().unwrap();
    rw.insert(Item {
        id: 7,
        name: "first".to_string(),
    })
    .unwrap();

    let result = rw.insert(Item {
        id: 7,
        name: "second".to_string(),
    });
    assert!(result.is_err());
}

#[test]
fn test_persistent_database_survives_reopen() {
    let dir = tempfile::tempdir().unwrap();
    let db_path = dir.path().join("persist.db");

    {
        let db = Builder::new().create(&MODELS, &db_path).unwrap();
        let rw = db.rw_transaction().unwrap();
        rw.insert(Item {
            id: 1,
            name: "durable".to_string(),
        })
        .unwrap();
        rw.commit().unwrap();
    }

    // Reopen
    let db = Builder::new().open(&MODELS, &db_path).unwrap();
    let r = db.r_transaction().unwrap();
    let item: Item = r.get().primary(1_u32).unwrap().unwrap();
    assert_eq!(item.name, "durable");
}

#[test]
fn test_bulk_insert_and_count() {
    let db = open_db();

    let rw = db.rw_transaction().unwrap();
    let count = 50;
    for i in 0..count {
        rw.insert(Item {
            id: i,
            name: format!("item-{:03}", i),
        })
        .unwrap();
    }
    rw.commit().unwrap();

    let r = db.r_transaction().unwrap();
    assert_eq!(r.len().primary::<Item>().unwrap(), count as u64);

    let items: Vec<Item> = r
        .scan()
        .primary::<Item>()
        .unwrap()
        .all()
        .unwrap()
        .collect::<Result<Vec<_>, _>>()
        .unwrap();
    assert_eq!(items.len(), count as usize);
}
