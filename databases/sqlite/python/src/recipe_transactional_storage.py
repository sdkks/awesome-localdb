"""
Recipe: Transactional Local Storage
Database: SQLite
Description: Demonstrates CRUD operations (create table, insert, update, select, delete)
             with WAL mode enabled, explicit transactions, and error handling.

Usage: python src/recipe_transactional_storage.py
"""

import sqlite3
import os
import sys


def main() -> None:
    db_path = os.path.join(os.path.dirname(__file__), "..", "recipe_storage.db")
    db_path = os.path.abspath(db_path)

    # ── 1. Setup ──────────────────────────────────────────────────────
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    print(f"Connected to {db_path} (WAL mode)")

    # ── 2. Schema ─────────────────────────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            year INTEGER,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    print("Table 'books' ready.")

    # ── 3. Write: Insert ──────────────────────────────────────────────
    try:
        with conn:
            conn.execute(
                "INSERT INTO books (title, author, year) VALUES (?, ?, ?)",
                ("The Pragmatic Programmer", "Andy Hunt & Dave Thomas", 1999),
            )
            conn.execute(
                "INSERT INTO books (title, author, year) VALUES (?, ?, ?)",
                ("Designing Data-Intensive Applications", "Martin Kleppmann", 2017),
            )
        print("Inserted 2 books.")
    except sqlite3.Error as e:
        print(f"Insert error: {e}", file=sys.stderr)

    # ── 4. Read: Select ───────────────────────────────────────────────
    rows = conn.execute("SELECT id, title, author, year FROM books").fetchall()
    print(f"\nAll books ({len(rows)}):")
    for row in rows:
        print(f"  [{row[0]}] {row[1]} by {row[2]} ({row[3]})")

    # ── 5. Update ─────────────────────────────────────────────────────
    try:
        with conn:
            conn.execute(
                "UPDATE books SET year = ? WHERE title = ?",
                (2020, "The Pragmatic Programmer"),
            )
        print("\nUpdated year for 'The Pragmatic Programmer'.")
    except sqlite3.Error as e:
        print(f"Update error: {e}", file=sys.stderr)

    # ── 6. Verify update ──────────────────────────────────────────────
    row = conn.execute(
        "SELECT title, year FROM books WHERE title = ?",
        ("The Pragmatic Programmer",),
    ).fetchone()
    print(f"  Verified: {row[0]} -> year {row[1]}")

    # ── 7. Delete ─────────────────────────────────────────────────────
    try:
        with conn:
            conn.execute(
                "DELETE FROM books WHERE title = ?",
                ("Designing Data-Intensive Applications",),
            )
        print("\nDeleted 'Designing Data-Intensive Applications'.")
        remaining = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
        print(f"  Remaining books: {remaining}")
    except sqlite3.Error as e:
        print(f"Delete error: {e}", file=sys.stderr)

    # ── 8. Cleanup ────────────────────────────────────────────────────
    conn.close()
    os.remove(db_path)
    print(f"\nCleaned up {db_path}.")


if __name__ == "__main__":
    main()
