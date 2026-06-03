//! Recipe: Document CRUD Operations
//! Database: SurrealDB
//! Description: Demonstrates embedded SurrealDB with document creation, reading,
//!     updating, deletion, SurrealQL queries, and record links.
//!
//! Usage: cargo run --bin recipe_document_crud

use serde::{Deserialize, Serialize};
use surrealdb::engine::local::Mem;
use surrealdb::Surreal;

#[derive(Debug, Serialize, Deserialize)]
struct Person {
    name: String,
    age: u8,
    city: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct Company {
    name: String,
    industry: String,
}

#[tokio::main]
async fn main() -> surrealdb::Result<()> {
    // 1. Setup — open embedded in-memory database
    let db = Surreal::new::<Mem>(()).await?;
    db.use_ns("test").use_db("test").await?;

    // 2. Create — insert documents with SurrealDB-generated IDs
    let alice: Option<Person> = db
        .create("person")
        .content(Person {
            name: "Alice".into(),
            age: 30,
            city: "London".into(),
        })
        .await?;
    println!("Created: {:?}", alice);

    let bob: Option<Person> = db
        .create("person")
        .content(Person {
            name: "Bob".into(),
            age: 25,
            city: "New York".into(),
        })
        .await?;
    println!("Created: {:?}", bob);

    // 3. Create with a specific ID
    let charlie: Option<Person> = db
        .create(("person", "charlie"))
        .content(Person {
            name: "Charlie".into(),
            age: 35,
            city: "Paris".into(),
        })
        .await?;
    println!("Created with specific ID: {:?}", charlie);

    // 4. Read — select by specific ID
    let found: Option<Person> = db.select(("person", "charlie")).await?;
    println!("\nFound by ID 'charlie': {:?}", found);

    // 5. Query — use SurrealQL to filter
    let mut result = db
        .query("SELECT * FROM person WHERE age > 20 ORDER BY age DESC")
        .await?;
    let people: Vec<Person> = result.take(0)?;
    println!("\nPeople over 20 (SurrealQL):");
    for p in &people {
        println!("  {} (age {}, {})", p.name, p.age, p.city);
    }

    // 6. Query with aggregation
    let mut result = db
        .query("SELECT count() AS total, math::mean(age) AS avg_age FROM person GROUP ALL")
        .await?;
    let stats: Vec<serde_json::Value> = result.take(0)?;
    println!("\nStats: {:?}", stats);

    // 7. Update — modify a document
    let updated: Option<Person> = db
        .update(("person", "charlie"))
        .merge(serde_json::json!({"age": 36, "city": "Berlin"}))
        .await?;
    println!("\nUpdated charlie: {:?}", updated);

    // 8. Create record links — relate persons to a company
    let company: Option<Company> = db
        .create(("company", "techcorp"))
        .content(Company {
            name: "TechCorp".into(),
            industry: "Software".into(),
        })
        .await?;
    println!("\nCreated company: {:?}", company);

    // Relate Alice and Bob to the company using graph edges
    let _ = db
        .query(
            "RELATE $person->works_at->$company"
        )
        .bind(("person", "person:charlie"))
        .bind(("company", "company:techcorp"))
        .await?;

    // 9. Delete — remove a record
    let deleted: Option<Person> = db.delete(("person", "charlie")).await?;
    println!("\nDeleted charlie: {:?}", deleted);

    // 10. Cleanup
    println!("\nDone.");
    Ok(())
}
