/// Integration tests for the libSQL Rust recipes.
/// These tests verify CRUD operations on an in-memory database.

use libsql::Builder;

#[tokio::test]
async fn test_crud_operations_in_memory() -> Result<(), Box<dyn std::error::Error>> {
    let db = Builder::new_local(":memory:").build().await?;
    let conn = db.connect()?;
    conn.execute_batch("PRAGMA foreign_keys = ON").await?;

    // Create
    conn.execute(
        "CREATE TABLE books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL
        )",
        (),
    ).await?;

    // Insert
    conn.execute(
        "INSERT INTO books (title, author) VALUES (?1, ?2)",
        libsql::params!["Test Book", "Test Author"],
    ).await?;

    let mut rows = conn.query("SELECT COUNT(*) FROM books", ()).await?;
    let count: i64 = rows.next().await?.unwrap().get(0)?;
    assert_eq!(count, 1);

    // Update
    conn.execute(
        "UPDATE books SET author = ?1 WHERE title = ?2",
        libsql::params!["Updated Author", "Test Book"],
    ).await?;

    let mut rows = conn.query(
        "SELECT author FROM books WHERE title = ?1",
        libsql::params!["Test Book"],
    ).await?;
    let author: String = rows.next().await?.unwrap().get(0)?;
    assert_eq!(author, "Updated Author");

    // Delete
    conn.execute(
        "DELETE FROM books WHERE title = ?1",
        libsql::params!["Test Book"],
    ).await?;

    let mut rows = conn.query("SELECT COUNT(*) FROM books", ()).await?;
    let count: i64 = rows.next().await?.unwrap().get(0)?;
    assert_eq!(count, 0);

    Ok(())
}
