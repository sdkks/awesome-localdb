//! Recipe: SQL Queries
//! Database: Limbo
//! Description: Demonstrates async CRUD operations (create table, insert, select,
//!              update, delete) with Limbo's fully asynchronous API.
//!              Note: Limbo is in beta — this recipe uses the 0.0.x API.
//!
//! Usage: cargo run --bin recipe_sql_queries

use limbo::{Builder, Value};
use std::fs;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let db_path = "recipe_sql_queries_limbo.db";

    // ── 1. Setup ──────────────────────────────────────────────────────
    let db = Builder::new_local(db_path).build().await?;
    let conn = db.connect()?;

    println!("Connected to {} (async I/O)", db_path);

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
    )
    .await?;
    println!("Table 'books' ready.");

    // ── 3. Write: Insert ──────────────────────────────────────────────
    conn.execute(
        "INSERT INTO books (title, author, year) VALUES (?1, ?2, ?3)",
        limbo::params!["The Pragmatic Programmer", "Andy Hunt & Dave Thomas", 1999],
    )
    .await?;
    conn.execute(
        "INSERT INTO books (title, author, year) VALUES (?1, ?2, ?3)",
        limbo::params!["Designing Data-Intensive Applications", "Martin Kleppmann", 2017],
    )
    .await?;
    println!("Inserted 2 books.");

    // ── 4. Read: Select ───────────────────────────────────────────────
    {
        let mut rows = conn
            .query(
                "SELECT id, title, author, year FROM books",
                (),
            )
            .await?;

        let mut books: Vec<(i64, String, String, i64)> = Vec::new();
        while let Some(row) = rows.next().await? {
            let id = match row.get_value(0)? {
                Value::Integer(v) => v,
                _ => continue,
            };
            let title = match row.get_value(1)? {
                Value::Text(v) => v,
                _ => continue,
            };
            let author = match row.get_value(2)? {
                Value::Text(v) => v,
                _ => continue,
            };
            let year = match row.get_value(3)? {
                Value::Integer(v) => v,
                _ => continue,
            };
            books.push((id, title, author, year));
        }

        println!("\nAll books ({}):", books.len());
        for (id, title, author, year) in &books {
            println!("  [{}] {} by {} ({})", id, title, author, year);
        }
    } // rows dropped here

    // ── 5. Update ─────────────────────────────────────────────────────
    conn.execute(
        "UPDATE books SET year = ?1 WHERE title = ?2",
        limbo::params![2020, "The Pragmatic Programmer"],
    )
    .await?;
    println!("\nUpdated year for 'The Pragmatic Programmer'.");

    // ── 6. Verify update ──────────────────────────────────────────────
    {
        let mut rows = conn
            .query(
                "SELECT title, year FROM books WHERE title = ?1",
                limbo::params!["The Pragmatic Programmer"],
            )
            .await?;

        if let Some(row) = rows.next().await? {
            let title = match row.get_value(0)? {
                Value::Text(v) => v,
                _ => String::from("<unexpected type>"),
            };
            let year = match row.get_value(1)? {
                Value::Integer(v) => v,
                _ => 0,
            };
            println!("  Verified: {} -> year {}", title, year);
        }
    }

    // ── 7. Delete ─────────────────────────────────────────────────────
    conn.execute(
        "DELETE FROM books WHERE title = ?1",
        limbo::params!["Designing Data-Intensive Applications"],
    )
    .await?;
    println!("\nDeleted 'Designing Data-Intensive Applications'.");

    {
        let mut rows = conn.query("SELECT COUNT(*) FROM books", ()).await?;
        if let Some(row) = rows.next().await? {
            if let Value::Integer(remaining) = row.get_value(0)? {
                println!("  Remaining books: {}", remaining);
            }
        }
    }

    // ── 8. Cleanup ────────────────────────────────────────────────────
    drop(conn);
    drop(db);
    fs::remove_file(db_path)?;
    println!("\nCleaned up {}.", db_path);

    Ok(())
}

