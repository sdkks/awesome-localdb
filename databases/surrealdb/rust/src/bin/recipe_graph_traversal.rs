//! Recipe: Graph Traversal
//! Database: SurrealDB
//! Description: Demonstrates SurrealDB's graph capabilities using record links
//!     and graph traversal operators (->, <-, <->) in SurrealQL.
//!
//! Usage: cargo run --bin recipe_graph_traversal

use serde::{Deserialize, Serialize};
use surrealdb::engine::local::Mem;
use surrealdb::Surreal;

#[derive(Debug, Serialize, Deserialize)]
struct Person {
    name: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct City {
    name: String,
    country: String,
}

#[tokio::main]
async fn main() -> surrealdb::Result<()> {
    // 1. Setup — open embedded in-memory database
    let db = Surreal::new::<Mem>(()).await?;
    db.use_ns("test").use_db("test").await?;

    // 2. Create nodes (people and cities)
    let alice: Option<Person> = db
        .create(("person", "alice"))
        .content(Person { name: "Alice".into() })
        .await?;
    let bob: Option<Person> = db
        .create(("person", "bob"))
        .content(Person { name: "Bob".into() })
        .await?;
    let carol: Option<Person> = db
        .create(("person", "carol"))
        .content(Person { name: "Carol".into() })
        .await?;
    let _london: Option<City> = db
        .create(("city", "london"))
        .content(City { name: "London".into(), country: "UK".into() })
        .await?;
    let _nyc: Option<City> = db
        .create(("city", "nyc"))
        .content(City { name: "New York".into(), country: "USA".into() })
        .await?;
    let _paris: Option<City> = db
        .create(("city", "paris"))
        .content(City { name: "Paris".into(), country: "France".into() })
        .await?;

    println!("Created nodes: {:?} / {:?} / {:?}", alice, bob, carol);

    // 3. Create edges — people live in cities, people know each other
    db.query("RELATE person:alice->lives_in->city:london").await?;
    db.query("RELATE person:bob->lives_in->city:nyc").await?;
    db.query("RELATE person:carol->lives_in->city:paris").await?;
    db.query("RELATE person:alice->knows->person:bob").await?;
    db.query("RELATE person:bob->knows->person:carol").await?;

    // 4. Graph traversal — find who Alice knows
    println!("\n=== Who does Alice know? ===");
    let mut result = db
        .query("SELECT ->knows->person.name AS knows FROM person:alice")
        .await?;
    let alice_knows: Vec<serde_json::Value> = result.take(0)?;
    for entry in &alice_knows {
        println!("  {:?}", entry);
    }

    // 5. Graph traversal — find where people Alice knows live
    println!("\n=== Where do Alice's friends live? ===");
    let mut result = db
        .query("SELECT ->knows->person->lives_in->city.name AS city FROM person:alice")
        .await?;
    let friend_cities: Vec<serde_json::Value> = result.take(0)?;
    for entry in &friend_cities {
        println!("  {:?}", entry);
    }

    // 6. Reverse traversal — who lives in London?
    println!("\n=== Who lives in London? ===");
    let mut result = db
        .query("SELECT <-lives_in<-person.name AS resident FROM city:london")
        .await?;
    let residents: Vec<serde_json::Value> = result.take(0)?;
    for entry in &residents {
        println!("  {:?}", entry);
    }

    // 7. Deep traversal — find people 2 hops away through knows edges
    println!("\n=== Who can Alice reach through friend-of-friend? ===");
    let mut result = db
        .query("SELECT ->knows->person->knows->person.name AS friend_of_friend FROM person:alice")
        .await?;
    let fof: Vec<serde_json::Value> = result.take(0)?;
    for entry in &fof {
        println!("  {:?}", entry);
    }

    // 8. Path query — find all people connected to Alice within 2 hops
    println!("\n=== All people within 2 hops of Alice ===");
    let mut result = db
        .query("SELECT ->knows->person.name AS name FROM person:alice")
        .await?;
    let direct: Vec<serde_json::Value> = result.take(0)?;
    println!("  Direct: {:?}", direct);

    let mut result = db
        .query("SELECT ->knows->person->knows->person.name AS name FROM person:alice")
        .await?;
    let indirect: Vec<serde_json::Value> = result.take(0)?;
    println!("  Indirect: {:?}", indirect);

    println!("\nDone.");
    Ok(())
}
