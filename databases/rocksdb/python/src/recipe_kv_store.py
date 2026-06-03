"""
Recipe: Basic KV Store Operations
Database: RocksDB
Description: Demonstrates opening a database, putting, getting, deleting
    keys, and performing an iterator scan.

Usage: python src/recipe_kv_store.py
"""

import os
import shutil
import rocksdbpy


def main():
    db_path = "/tmp/rocksdb_recipe_kv_store"

    # 1. Setup — open the database with default options
    db = rocksdbpy.open_default(db_path)

    # 2. Write — insert key-value pairs
    db.set(b"name", b"RocksDB")
    db.set(b"type", b"key-value")
    db.set(b"year", b"2013")
    db.set(b"license", b"Apache-2.0")

    # 3. Read — retrieve individual keys
    name = db.get(b"name")
    print(f"name = {name.decode()}")

    db_type = db.get(b"type")
    print(f"type = {db_type.decode()}")

    # 4. Delete — remove a key
    db.delete(b"license")
    deleted = db.get(b"license")
    print(f"license after delete = {deleted}")

    # 5. Scan — iterate over all entries
    print("\nAll entries:")
    for key, value in db.iterator():
        print(f"  {key.decode()} => {value.decode()}")

    # 6. Cleanup
    db.close()
    shutil.rmtree(db_path, ignore_errors=True)
    print("\nDone.")


if __name__ == "__main__":
    main()
