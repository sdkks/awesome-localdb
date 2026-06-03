//! Recipe: In-Memory Cache
//! Database: SQLite
//! Description: Demonstrates using SQLite's in-memory mode as a fast local cache.
//!              Shows key-value storage with TTL-like semantics and bulk operations.
//!
//! Usage: cargo run --bin recipe_in_memory_cache

use rusqlite::{params, Connection, Result};
use std::time::Instant;

fn main() -> Result<()> {
    // ── 1. Setup: In-memory database ──────────────────────────────────
    let conn = Connection::open_in_memory()?;
    conn.execute_batch("PRAGMA journal_mode=OFF")?;
    conn.execute_batch("PRAGMA synchronous=OFF")?;
    println!("Connected to :memory: (no disk I/O)");

    // ── 2. Schema ─────────────────────────────────────────────────────
    conn.execute(
        "CREATE TABLE cache (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            expires_at REAL NOT NULL
        )",
        [],
    )?;
    conn.execute("CREATE INDEX idx_expires ON cache(expires_at)", [])?;
    println!("Cache table ready.");

    // ── 3. Write: Populate cache ──────────────────────────────────────
    let ttl_secs = 3600.0; // 1 hour
    let base_time = 0.0; // Simulated base time

    let items = vec![
        ("user:1", r#"{"name": "Alice", "role": "admin"}"#, base_time + ttl_secs),
        ("user:2", r#"{"name": "Bob", "role": "editor"}"#, base_time + ttl_secs),
        ("user:3", r#"{"name": "Carol", "role": "viewer"}"#, base_time + 600.0),
    ];

    for (key, value, expires) in &items {
        conn.execute(
            "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?1, ?2, ?3)",
            params![key, value, expires],
        )?;
    }
    println!("Cached {} entries.", items.len());

    // ── 4. Read: Lookup ───────────────────────────────────────────────
    for key in ["user:1", "user:2", "user:99"] {
        let result: std::result::Result<(String, f64), _> = conn.query_row(
            "SELECT value, expires_at FROM cache WHERE key = ?1",
            params![key],
            |row| Ok((row.get(0)?, row.get(1)?)),
        );

        match result {
            Ok((value, _expires)) => {
                println!("  HIT  {} -> {}", key, value);
            }
            Err(_) => {
                println!("  MISS {}", key);
            }
        }
    }

    // ── 5. Bulk expiry cleanup ────────────────────────────────────────
    conn.execute("DELETE FROM cache WHERE expires_at <= ?1", params![base_time])?;
    let count: i64 = conn.query_row("SELECT COUNT(*) FROM cache", [], |row| row.get(0))?;
    println!("\nActive cache entries after cleanup: {}", count);

    // ── 6. Performance note ───────────────────────────────────────────
    let perf_start = Instant::now();
    for i in 0..1000 {
        conn.execute(
            "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?1, ?2, ?3)",
            params![format!("perf:{}", i), format!("data-{}", i), base_time + 60.0],
        )?;
    }
    let elapsed = perf_start.elapsed();
    println!(
        "Inserted 1,000 rows in {:.1} ms ({:.3} ms/row)",
        elapsed.as_secs_f64() * 1000.0,
        elapsed.as_secs_f64()
    );

    // ── 7. Cleanup ────────────────────────────────────────────────────
    drop(conn);
    println!("Connection closed (in-memory data discarded).");

    Ok(())
}
