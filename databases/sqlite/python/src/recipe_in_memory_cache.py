"""
Recipe: In-Memory Cache
Database: SQLite
Description: Demonstrates using SQLite's :memory: mode as a fast local cache.
             Shows key-value storage with TTL-like semantics and bulk operations.

Usage: python src/recipe_in_memory_cache.py
"""

import sqlite3
import time


def main() -> None:
    # ── 1. Setup: In-memory database ──────────────────────────────────
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA journal_mode=OFF")  # No need for WAL in memory
    conn.execute("PRAGMA synchronous=OFF")  # Max speed for cache use
    print("Connected to :memory: (no disk I/O)")

    # ── 2. Schema ─────────────────────────────────────────────────────
    conn.execute("""
        CREATE TABLE cache (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            expires_at REAL NOT NULL
        )
    """)
    conn.execute("CREATE INDEX idx_expires ON cache(expires_at)")
    conn.commit()
    print("Cache table ready.")

    # ── 3. Write: Populate cache ──────────────────────────────────────
    now = time.time()
    ttl = 3600  # 1 hour in seconds

    items = [
        ("user:1", '{"name": "Alice", "role": "admin"}', now + ttl),
        ("user:2", '{"name": "Bob", "role": "editor"}', now + ttl),
        ("user:3", '{"name": "Carol", "role": "viewer"}', now + 600),  # 10 min TTL
    ]

    with conn:
        conn.executemany(
            "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, ?)",
            items,
        )
    print(f"Cached {len(items)} entries.")

    # ── 4. Read: Lookup with expiry check ─────────────────────────────
    def cache_get(key: str) -> str | None:
        row = conn.execute(
            "SELECT value, expires_at FROM cache WHERE key = ?", (key,)
        ).fetchone()
        if row is None:
            return None
        value, expires = row
        if time.time() > expires:
            conn.execute("DELETE FROM cache WHERE key = ?", (key,))
            conn.commit()
            return None
        return value

    for key in ["user:1", "user:2", "user:99"]:
        value = cache_get(key)
        if value:
            print(f"  HIT  {key} -> {value}")
        else:
            print(f"  MISS {key}")

    # ── 5. Bulk read with expiry cleanup ──────────────────────────────
    conn.execute("DELETE FROM cache WHERE expires_at <= ?", (time.time(),))
    conn.commit()

    count = conn.execute("SELECT COUNT(*) FROM cache").fetchone()[0]
    print(f"\nActive cache entries after cleanup: {count}")

    # ── 6. Performance note ───────────────────────────────────────────
    start = time.perf_counter()
    for i in range(1000):
        conn.execute(
            "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, ?)",
            (f"perf:{i}", f"data-{i}", now + 60),
        )
    conn.commit()
    elapsed = (time.perf_counter() - start) * 1000
    print(f"Inserted 1,000 rows in {elapsed:.1f} ms ({elapsed/1000:.3f} ms/row)")

    # ── 7. Cleanup ────────────────────────────────────────────────────
    conn.close()
    print("Connection closed (in-memory data discarded).")


if __name__ == "__main__":
    main()
