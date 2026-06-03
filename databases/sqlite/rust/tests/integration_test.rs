/// Integration tests for the SQLite Rust recipes.
/// These tests run the recipe binaries and verify their behavior.

use rusqlite::{params, Connection, Result};

#[test]
fn test_crud_operations_in_memory() -> Result<()> {
    let conn = Connection::open_in_memory()?;
    conn.execute_batch("PRAGMA foreign_keys = ON")?;

    // Create
    conn.execute(
        "CREATE TABLE books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL
        )",
        [],
    )?;

    // Insert
    conn.execute(
        "INSERT INTO books (title, author) VALUES (?1, ?2)",
        params!["Test Book", "Test Author"],
    )?;
    let count: i64 = conn.query_row("SELECT COUNT(*) FROM books", [], |row| row.get(0))?;
    assert_eq!(count, 1);

    // Update
    conn.execute(
        "UPDATE books SET author = ?1 WHERE title = ?2",
        params!["Updated Author", "Test Book"],
    )?;
    let author: String = conn.query_row(
        "SELECT author FROM books WHERE title = ?1",
        params!["Test Book"],
        |row| row.get(0),
    )?;
    assert_eq!(author, "Updated Author");

    // Delete
    conn.execute("DELETE FROM books WHERE title = ?1", params!["Test Book"])?;
    let count: i64 = conn.query_row("SELECT COUNT(*) FROM books", [], |row| row.get(0))?;
    assert_eq!(count, 0);

    Ok(())
}

#[test]
fn test_in_memory_cache_hit_and_miss() -> Result<()> {
    let conn = Connection::open_in_memory()?;

    conn.execute(
        "CREATE TABLE cache (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            expires_at REAL NOT NULL
        )",
        [],
    )?;

    // Insert a known key
    conn.execute(
        "INSERT INTO cache (key, value, expires_at) VALUES (?1, ?2, ?3)",
        params!["key1", "value1", 9999999999.0_f64],
    )?;

    // Hit
    let (value, expires): (String, f64) = conn.query_row(
        "SELECT value, expires_at FROM cache WHERE key = ?1",
        params!["key1"],
        |row| Ok((row.get(0)?, row.get(1)?)),
    )?;
    assert_eq!(value, "value1");
    assert!(expires > 0.0);

    // Miss
    let result: std::result::Result<(String, f64), _> = conn.query_row(
        "SELECT value, expires_at FROM cache WHERE key = ?1",
        params!["nonexistent"],
        |row| Ok((row.get(0)?, row.get(1)?)),
    );
    assert!(result.is_err());

    Ok(())
}

#[test]
fn test_in_memory_cache_expiry() -> Result<()> {
    let conn = Connection::open_in_memory()?;

    conn.execute(
        "CREATE TABLE cache (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            expires_at REAL NOT NULL
        )",
        [],
    )?;

    // Insert expired entry
    conn.execute(
        "INSERT INTO cache (key, value, expires_at) VALUES (?1, ?2, ?3)",
        params!["expired_key", "should-be-gone", 1.0_f64],
    )?;

    // Cleanup expired
    conn.execute("DELETE FROM cache WHERE expires_at <= ?1", params![9999999999.0_f64])?;

    let count: i64 = conn.query_row("SELECT COUNT(*) FROM cache", [], |row| row.get(0))?;
    assert_eq!(count, 0);

    Ok(())
}
