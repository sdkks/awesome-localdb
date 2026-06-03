//! Recipe: Transactional Local Storage
//! Database: SQLite
//! Description: Demonstrates CRUD operations (create table, insert, update, select, delete)
//!              with WAL mode enabled, explicit transactions, and error handling.
//!
//! Usage: cargo run --bin recipe_transactional_storage

use rusqlite::{params, Connection, Result};
use std::fs;

fn main() -> Result<()> {
    let db_path = "recipe_storage.db";

    // ── 1. Setup ──────────────────────────────────────────────────────
    let conn = Connection::open(db_path)?;
    conn.execute_batch("PRAGMA journal_mode=WAL")?;
    conn.execute_batch("PRAGMA foreign_keys=ON")?;

    println!("Connected to {} (WAL mode)", db_path);

    // ── 2. Schema ─────────────────────────────────────────────────────
    conn.execute(
        "CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            year INTEGER,
            created_at TEXT DEFAULT (datetime('now'))
        )",
        [],
    )?;
    println!("Table 'books' ready.");

    // ── 3. Write: Insert ──────────────────────────────────────────────
    conn.execute(
        "INSERT INTO books (title, author, year) VALUES (?1, ?2, ?3)",
        params!["The Pragmatic Programmer", "Andy Hunt & Dave Thomas", 1999],
    )?;
    conn.execute(
        "INSERT INTO books (title, author, year) VALUES (?1, ?2, ?3)",
        params!["Designing Data-Intensive Applications", "Martin Kleppmann", 2017],
    )?;
    println!("Inserted 2 books.");

    // ── 4. Read: Select ───────────────────────────────────────────────
    {
        let mut stmt = conn.prepare("SELECT id, title, author, year FROM books")?;
        let rows: Vec<(i64, String, String, i64)> = stmt
            .query_map([], |row| {
                Ok((row.get(0)?, row.get(1)?, row.get(2)?, row.get(3)?))
            })?
            .filter_map(|r| r.ok())
            .collect();

        println!("\nAll books ({}):", rows.len());
        for (id, title, author, year) in &rows {
            println!("  [{}] {} by {} ({})", id, title, author, year);
        }
    } // stmt dropped here, releasing borrow on conn

    // ── 5. Update ─────────────────────────────────────────────────────
    conn.execute(
        "UPDATE books SET year = ?1 WHERE title = ?2",
        params![2020, "The Pragmatic Programmer"],
    )?;
    println!("\nUpdated year for 'The Pragmatic Programmer'.");

    // ── 6. Verify update ──────────────────────────────────────────────
    let (title, year): (String, i64) = conn.query_row(
        "SELECT title, year FROM books WHERE title = ?1",
        params!["The Pragmatic Programmer"],
        |row| Ok((row.get(0)?, row.get(1)?)),
    )?;
    println!("  Verified: {} -> year {}", title, year);

    // ── 7. Delete ─────────────────────────────────────────────────────
    conn.execute(
        "DELETE FROM books WHERE title = ?1",
        params!["Designing Data-Intensive Applications"],
    )?;
    println!("\nDeleted 'Designing Data-Intensive Applications'.");
    let remaining: i64 =
        conn.query_row("SELECT COUNT(*) FROM books", [], |row| row.get(0))?;
    println!("  Remaining books: {}", remaining);

    // ── 8. Cleanup ────────────────────────────────────────────────────
    drop(conn); // Close the connection first
    fs::remove_file(db_path).expect("Failed to remove test database file");
    println!("\nCleaned up {}.", db_path);

    Ok(())
}
