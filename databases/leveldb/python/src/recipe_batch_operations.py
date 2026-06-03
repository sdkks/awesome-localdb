"""
Recipe: WriteBatch Operations
Database: LevelDB
Description: Demonstrates using WriteBatch for atomic batch writes,
    batching multiple puts and deletes in a single commit.

Usage: python src/recipe_batch_operations.py
"""

import os
import shutil
import plyvel


def main():
    db_path = "/tmp/leveldb_recipe_batch_operations"

    # 1. Setup -- open the database
    db = plyvel.DB(db_path, create_if_missing=True)

    # 2. WriteBatch -- stage multiple operations atomically
    wb = db.write_batch()
    for i in range(1, 6):
        key = f"item:{i}".encode()
        value = f"value-{i}".encode()
        wb.put(key, value)
    wb.delete(b"item:3")  # Remove item:3 from the batch
    wb.write()

    # 3. Read back -- verify batch results
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
