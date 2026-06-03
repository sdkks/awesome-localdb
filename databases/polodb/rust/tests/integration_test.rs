use polodb_core::bson::{doc, Document};
use polodb_core::{CollectionT, Database};
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize, PartialEq)]
struct Book {
    title: String,
    author: String,
    year: u32,
}

#[test]
fn test_open_and_insert_typed() {
    let dir = tempfile::tempdir().unwrap();
    let db = Database::open_path(dir.path().join("test.polo")).unwrap();

    let collection = db.collection::<Book>("books");
    collection
        .insert_one(Book {
            title: "1984".into(),
            author: "George Orwell".into(),
            year: 1949,
        })
        .unwrap();

    let results: Vec<Book> = collection
        .find(doc! {})
        .run()
        .unwrap()
        .filter_map(|r| r.ok())
        .collect();

    assert_eq!(results.len(), 1);
    assert_eq!(results[0].title, "1984");
    assert_eq!(results[0].author, "George Orwell");
}

#[test]
fn test_insert_many_bson_documents() {
    let dir = tempfile::tempdir().unwrap();
    let db = Database::open_path(dir.path().join("bson.polo")).unwrap();

    let collection = db.collection::<Document>("books");
    collection
        .insert_many(vec![
            doc! { "title": "1984", "author": "George Orwell", "year": 1949 },
            doc! { "title": "Dune", "author": "Frank Herbert", "year": 1965 },
            doc! { "title": "Foundation", "author": "Isaac Asimov", "year": 1951 },
        ])
        .unwrap();

    let all: Vec<Document> = collection
        .find(doc! {})
        .run()
        .unwrap()
        .filter_map(|r| r.ok())
        .collect();
    assert_eq!(all.len(), 3);
}

#[test]
fn test_find_with_filter() {
    let dir = tempfile::tempdir().unwrap();
    let db = Database::open_path(dir.path().join("filter.polo")).unwrap();

    let collection = db.collection::<Document>("books");
    collection
        .insert_many(vec![
            doc! { "title": "1984", "author": "George Orwell", "year": 1949 },
            doc! { "title": "Animal Farm", "author": "George Orwell", "year": 1945 },
            doc! { "title": "Dune", "author": "Frank Herbert", "year": 1965 },
        ])
        .unwrap();

    let orwell: Vec<Document> = collection
        .find(doc! { "author": "George Orwell" })
        .run()
        .unwrap()
        .filter_map(|r| r.ok())
        .collect();

    assert_eq!(orwell.len(), 2, "Should find 2 Orwell books");
    let titles: Vec<&str> = orwell
        .iter()
        .map(|d| d.get_str("title").unwrap())
        .collect();
    assert!(titles.contains(&"1984"));
    assert!(titles.contains(&"Animal Farm"));
}

#[test]
fn test_delete_many() {
    let dir = tempfile::tempdir().unwrap();
    let db = Database::open_path(dir.path().join("delete.polo")).unwrap();

    let collection = db.collection::<Document>("books");
    collection
        .insert_many(vec![
            doc! { "title": "1984", "author": "George Orwell" },
            doc! { "title": "Dune", "author": "Frank Herbert" },
        ])
        .unwrap();

    collection
        .delete_many(doc! { "title": "Dune" })
        .unwrap();

    let remaining: Vec<Document> = collection
        .find(doc! {})
        .run()
        .unwrap()
        .filter_map(|r| r.ok())
        .collect();

    assert_eq!(remaining.len(), 1);
    assert_eq!(remaining[0].get_str("title").unwrap(), "1984");
}

#[test]
fn test_explicit_transaction_commit() {
    let dir = tempfile::tempdir().unwrap();
    let db = Database::open_path(dir.path().join("txn.polo")).unwrap();

    let txn = db.start_transaction().unwrap();
    {
        let collection = txn.collection::<Document>("books");
        collection
            .insert_one(doc! { "title": "Foundation", "author": "Isaac Asimov" })
            .unwrap();
    }
    txn.commit().unwrap();

    let collection = db.collection::<Document>("books");
    let results: Vec<Document> = collection
        .find(doc! {})
        .run()
        .unwrap()
        .filter_map(|r| r.ok())
        .collect();
    assert_eq!(results.len(), 1);
}

#[test]
fn test_transaction_rollback_on_drop() {
    let dir = tempfile::tempdir().unwrap();
    let db = Database::open_path(dir.path().join("rollback.polo")).unwrap();

    // Insert initial data outside transaction (auto-transaction)
    let collection = db.collection::<Document>("books");
    collection
        .insert_one(doc! { "title": "Keep Me", "author": "Permanent" })
        .unwrap();

    // Start a transaction, insert, then rollback by dropping without commit
    let txn = db.start_transaction().unwrap();
    {
        let txn_collection = txn.collection::<Document>("books");
        txn_collection
            .insert_one(doc! { "title": "Discard Me", "author": "Temporary" })
            .unwrap();
    }
    drop(txn); // Rollback -- transaction never committed

    let results: Vec<Document> = collection
        .find(doc! {})
        .run()
        .unwrap()
        .filter_map(|r| r.ok())
        .collect();
    assert_eq!(results.len(), 1);
    assert_eq!(results[0].get_str("title").unwrap(), "Keep Me");
}

#[test]
fn test_empty_find_result() {
    let dir = tempfile::tempdir().unwrap();
    let db = Database::open_path(dir.path().join("empty.polo")).unwrap();

    let collection = db.collection::<Document>("books");
    let results: Vec<Document> = collection
        .find(doc! { "author": "Nonexistent" })
        .run()
        .unwrap()
        .filter_map(|r| r.ok())
        .collect();

    assert!(results.is_empty());
}

#[test]
fn test_count_documents() {
    let dir = tempfile::tempdir().unwrap();
    let db = Database::open_path(dir.path().join("count.polo")).unwrap();

    let collection = db.collection::<Document>("books");
    collection
        .insert_many(vec![
            doc! { "title": "A", "tags": ["x"] },
            doc! { "title": "B", "tags": ["x", "y"] },
            doc! { "title": "C", "tags": ["y"] },
        ])
        .unwrap();

    let total = collection.find(doc! {}).run().unwrap().count();
    assert_eq!(total, 3);
}
