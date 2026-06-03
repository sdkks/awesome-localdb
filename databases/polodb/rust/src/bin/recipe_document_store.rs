//! Recipe: Document Store CRUD Operations
//! Database: PoloDB
//! Description: Demonstrates creating a database, inserting documents with
//!     typed structs and raw BSON, finding with filters, updating, deleting,
//!     and explicit transaction control using the polodb_core MongoDB-like API.
//!
//! Usage: cargo run --bin recipe_document_store

use polodb_core::bson::{doc, Document};
use polodb_core::{CollectionT, Database};
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
struct Recipe {
    title: String,
    author: String,
    year: u32,
    tags: Vec<String>,
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let dir = tempfile::tempdir()?;
    let db_path = dir.path().join("recipes.polo");

    // 1. Setup -- open or create the database
    let db = Database::open_path(&db_path)?;

    // 2. Insert typed structs
    let collection = db.collection::<Recipe>("recipes");
    collection.insert_one(Recipe {
        title: "The Three-Body Problem".into(),
        author: "Liu Cixin".into(),
        year: 2008,
        tags: vec!["sci-fi".into(), "Chinese".into()],
    })?;

    // 3. Insert raw BSON documents
    let raw_collection = db.collection::<Document>("recipes");
    raw_collection.insert_many(vec![
        doc! {
            "title": "1984",
            "author": "George Orwell",
            "year": 1949,
            "tags": ["dystopian", "classic"],
        },
        doc! {
            "title": "Animal Farm",
            "author": "George Orwell",
            "year": 1945,
            "tags": ["allegory", "classic"],
        },
        doc! {
            "title": "Dune",
            "author": "Frank Herbert",
            "year": 1965,
            "tags": ["sci-fi", "classic"],
        },
    ])?;

    // 4. Find with filter
    println!("Books by George Orwell:");
    let results = raw_collection
        .find(doc! { "author": "George Orwell" })
        .run()?;
    for result in results {
        let doc = result?;
        println!(
            "  {} ({})",
            doc.get_str("title").unwrap_or("unknown"),
            doc.get_i32("year").unwrap_or(0)
        );
    }

    // 5. Update -- using typed collection, we'd need to delete + insert or use raw BSON
    // PoloDB doesn't have a direct update_one, so we demonstrate find-and-replace pattern
    println!("\nUpdating '1984' year to 1950 (delete + insert)...");
    let docs_to_update: Vec<Document> = raw_collection
        .find(doc! { "title": "1984" })
        .run()?
        .filter_map(|r| r.ok())
        .collect();
    for mut doc in docs_to_update {
        doc.insert("year", 1950);
        raw_collection.insert_one(doc)?;
    }

    let results = raw_collection
        .find(doc! { "title": "1984" })
        .run()?;
    for result in results {
        let doc = result?;
        println!("  1984 year = {}", doc.get_i32("year").unwrap_or(0));
    }

    // 6. Delete
    println!("\nDeleting 'Dune'...");
    raw_collection.delete_many(doc! { "title": "Dune" })?;

    let remaining: Vec<Document> = raw_collection.find(doc! {}).run()?
        .filter_map(|r| r.ok())
        .collect();
    println!("Remaining documents: {}", remaining.len());
    for doc in &remaining {
        println!(
            "  {} by {}",
            doc.get_str("title").unwrap_or("unknown"),
            doc.get_str("author").unwrap_or("unknown")
        );
    }

    // 7. Explicit transaction
    println!("\nExplicit transaction -- inserting new book...");
    let txn = db.start_transaction()?;
    {
        let txn_collection = txn.collection::<Document>("recipes");
        txn_collection.insert_one(doc! {
            "title": "Foundation",
            "author": "Isaac Asimov",
            "year": 1951,
            "tags": ["sci-fi", "classic"],
        })?;
    }
    txn.commit()?;

    let final_count = raw_collection.find(doc! {}).run()?.count();
    println!("Final document count: {}", final_count);

    // 8. Count with filter (exact field match -- PoloDB does not do array element matching)
    let classic_count = raw_collection
        .find(doc! { "author": "George Orwell" })
        .run()?
        .count();
    println!("Books by George Orwell: {}", classic_count);

    println!("\nDone.");
    Ok(())
}
