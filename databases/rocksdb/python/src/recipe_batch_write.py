"""
Recipe: WriteBatch Operations
Database: RocksDB
Description: Demonstrates using WriteBatch for high-throughput atomic writes,
    batching multiple puts and deletes in a single commit.

Usage: python src/recipe_batch_write.py
"""

import os
import shutil
import rocksdbpy


def main():
    db_path = "/tmp/rocksdb_recipe_batch_write"

    # 1. Setup — open the database
    db = rocksdbpy.open_default(db_path)

    # 2. WriteBatch — stage multiple operations atomically
    batch = rocksdbpy.WriteBatch()
    for i in range(1, 6):
        key = f"item:{i}".encode()
        value = f"value-{i}".encode()
        batch.add(key, value)
    batch.delete(b"item:3")  # Remove item:3 from the batch
    db.write(batch)

    # 3. Read back — verify batch results
    print("After WriteBatch:")
    for i in range(1, 6):
        key = f"item:{i}".encode()
        value = db.get(key)
        status = value.decode() if value else "(deleted)"
        print(f"  {key.decode()} => {status}")

    # 4. Cleanup
    db.close()
    shutil.rmtree(db_path, ignore_errors=True)
    print("\nDone.")


if __name__ == "__main__":
    main()
