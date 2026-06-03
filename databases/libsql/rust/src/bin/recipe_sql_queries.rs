//! Recipe: SQL Queries
//! Database: libSQL
//! Description: Demonstrates async CRUD operations (create table, insert, update, select, delete)
//!              with WAL mode enabled, explicit transactions, and error handling.
//!
//! Usage: cargo run --bin recipe_sql_queries

use libsql::Builder;
use std::fs;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let db_path = "recipe_sql_queries.db";

    // ── 1. Setup ──────────────────────────────────────────────────────
    let db = Builder::new_local(db_path).build().await?;
    let conn = db.connect()?;
    conn.execute_batch("PRAGMA journal_mode=WAL").await?;
    conn.execute_batch("PRAGMA foreign_keys=ON").await?;

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
        (),
    ).await?;
    println!("Table 'books' ready.");

    // ── 3. Write: Insert ──────────────────────────────────────────────
    conn.execute(
        "INSERT INTO books (title, author, year) VALUES (?1, ?2, ?3)",
        libsql::params!["The Pragmatic Programmer", "Andy Hunt & Dave Thomas", 1999],
    ).await?;
    conn.execute(
        "INSERT INTO books (title, author, year) VALUES (?1, ?2, ?3)",
        libsql::params!["Designing Data-Intensive Applications", "Martin Kleppmann", 2017],
    ).await?;
    println!("Inserted 2 books.");

    // ── 4. Read: Select ───────────────────────────────────────────────
    {
        let mut rows = conn.query(
            "SELECT id, title, author, year FROM books", (),
        ).await?;

        let mut books: Vec<(i64, String, String, i64)> = Vec::new();
        while let Some(row) = rows.next().await? {
            books.push((
                row.get(0)?,
                row.get(1)?,
                row.get(2)?,
                row.get(3)?,
            ));
        }

        println!("\nAll books ({}):", books.len());
        for (id, title, author, year) in &books {
            println!("  [{}] {} by {} ({})", id, title, author, year);
        }
    } // rows dropped here, releasing borrow on conn

    // ── 5. Update ─────────────────────────────────────────────────────
    conn.execute(
        "UPDATE books SET year = ?1 WHERE title = ?2",
        libsql::params![2020, "The Pragmatic Programmer"],
    ).await?;
    println!("\nUpdated year for 'The Pragmatic Programmer'.");

    // ── 6. Verify update ──────────────────────────────────────────────
    {
        let mut rows = conn.query(
            "SELECT title, year FROM books WHERE title = ?1",
            libsql::params!["The Pragmatic Programmer"],
        ).await?;

        if let Some(row) = rows.next().await? {
            let title: String = row.get(0)?;
            let year: i64 = row.get(1)?;
            println!("  Verified: {} -> year {}", title, year);
        }
    }

    // ── 7. Delete ─────────────────────────────────────────────────────
    conn.execute(
        "DELETE FROM books WHERE title = ?1",
        libsql::params!["Designing Data-Intensive Applications"],
    ).await?;
    println!("\nDeleted 'Designing Data-Intensive Applications'.");

    {
        let mut rows = conn.query("SELECT COUNT(*) FROM books", ()).await?;
        if let Some(row) = rows.next().await? {
            let remaining: i64 = row.get(0)?;
            println!("  Remaining books: {}", remaining);
        }
    }

    // ── 8. Cleanup ────────────────────────────────────────────────────
    drop(conn);
    drop(db);
    fs::remove_file(db_path)?;
    println!("\nCleaned up {}.", db_path);

    Ok(())
}
