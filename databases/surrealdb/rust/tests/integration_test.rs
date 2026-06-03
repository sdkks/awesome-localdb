use surrealdb::engine::local::Mem;
use surrealdb::Surreal;

#[derive(Debug, serde::Serialize, serde::Deserialize)]
struct TestRecord {
    field: Option<String>,
    num: Option<i64>,
}

#[derive(Debug, serde::Serialize, serde::Deserialize)]
struct Person {
    name: Option<String>,
    score: Option<i64>,
}

#[derive(Debug, serde::Serialize, serde::Deserialize)]
struct Todo {
    title: String,
    done: bool,
}

#[tokio::test]
async fn test_document_crud_operations() {
    let db = Surreal::new::<Mem>(()).await.unwrap();
    db.use_ns("test").use_db("test").await.unwrap();

    // Create a document via SurrealQL
    db.query("CREATE test_record CONTENT { field: 'value', num: 42 }")
        .await
        .unwrap();

    // Read back via query
    let mut result = db
        .query("SELECT * FROM test_record WHERE num = 42")
        .await
        .unwrap();
    let records: Vec<TestRecord> = result.take(0).unwrap();
    assert!(!records.is_empty());
    assert_eq!(records[0].num, Some(42));
    assert_eq!(records[0].field.as_deref(), Some("value"));
}

#[tokio::test]
async fn test_surrealdb_query_filter() {
    let db = Surreal::new::<Mem>(()).await.unwrap();
    db.use_ns("test").use_db("test").await.unwrap();

    // Insert multiple records via SurrealQL
    for i in 0..5 {
        db.query(format!(
            "CREATE person CONTENT {{ name: 'Person{}', score: {} }}",
            i, i * 10
        ))
        .await
        .unwrap();
    }

    // Query with filter
    let mut result = db
        .query("SELECT * FROM person WHERE score > 20 ORDER BY score DESC")
        .await
        .unwrap();
    let people: Vec<Person> = result.take(0).unwrap();
    assert_eq!(people.len(), 2);
    let scores: Vec<i64> = people.iter().map(|p| p.score.unwrap()).collect();
    assert!(scores[0] > scores[1]);
}

#[tokio::test]
async fn test_graph_edges_and_traversal() {
    let db = Surreal::new::<Mem>(()).await.unwrap();
    db.use_ns("test").use_db("test").await.unwrap();

    // Create nodes via SurrealQL
    db.query("CREATE person:a CONTENT { name: 'A' }")
        .await
        .unwrap();
    db.query("CREATE person:b CONTENT { name: 'B' }")
        .await
        .unwrap();

    // Create an edge: A -> knows -> B
    db.query("RELATE person:a->knows->person:b")
        .await
        .unwrap();

    // Traverse from A — check the query succeeds and returns results
    let result = db
        .query("SELECT ->knows->person.name AS knows FROM person:a")
        .await
        .unwrap();
    // Verify we got results — query should contain B
    assert!(format!("{:?}", result).contains("B"));
}

#[tokio::test]
async fn test_update_and_delete() {
    let db = Surreal::new::<Mem>(()).await.unwrap();
    db.use_ns("test").use_db("test").await.unwrap();

    // Create via SurrealQL
    db.query("CREATE todo:task1 CONTENT { title: 'Original', done: false }")
        .await
        .unwrap();

    // Verify creation via select
    let created: Option<Todo> = db.select(("todo", "task1")).await.unwrap();
    assert!(created.is_some());
    assert_eq!(created.as_ref().unwrap().title, "Original");
    assert!(!created.as_ref().unwrap().done);

    // Update via SurrealQL
    db.query("UPDATE todo:task1 SET title = 'Updated', done = true")
        .await
        .unwrap();
    let updated: Option<Todo> = db.select(("todo", "task1")).await.unwrap();
    assert!(updated.is_some());
    assert_eq!(updated.as_ref().unwrap().title, "Updated");
    assert!(updated.as_ref().unwrap().done);

    // Delete
    let deleted: Option<Todo> = db.delete(("todo", "task1")).await.unwrap();
    assert!(deleted.is_some());

    // Verify deletion
    let not_found: Option<Todo> = db.select(("todo", "task1")).await.unwrap();
    assert!(not_found.is_none());
}

#[tokio::test]
async fn test_aggregation_query() {
    let db = Surreal::new::<Mem>(()).await.unwrap();
    db.use_ns("test").use_db("test").await.unwrap();

    for i in 0..10 {
        db.query(format!(
            "CREATE item CONTENT {{ value: {} }}",
            i + 1
        ))
        .await
        .unwrap();
    }

    let mut result = db
        .query("SELECT count() AS total, math::mean(value) AS avg_value FROM item GROUP ALL")
        .await
        .unwrap();
    let stats: Vec<serde_json::Value> = result.take(0).unwrap();
    assert_eq!(stats[0]["total"], 10);
    let avg = stats[0]["avg_value"].as_f64().unwrap();
    assert!((avg - 5.5).abs() < 0.01);
}
