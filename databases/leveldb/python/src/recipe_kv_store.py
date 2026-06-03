"""
Recipe: Basic KV Store Operations
Database: LevelDB
Description: Demonstrates opening a database, putting, getting, deleting
    keys, and performing an iterator scan.

Usage: python src/recipe_kv_store.py
"""

import os
import shutil
import plyvel


def main():
    db_path = "/tmp/leveldb_recipe_kv_store"

    # 1. Setup -- open the database (creates if missing)
    db = plyvel.DB(db_path, create_if_missing=True)

    # 2. Write -- insert key-value pairs
    db.put(b"name", b"LevelDB")
    db.put(b"type", b"key-value")
    db.put(b"year", b"2011")
    db.put(b"license", b"BSD-3-Clause")

    # 3. Read -- retrieve individual keys
    name = db.get(b"name")
    print(f"name = {name.decode()}")

    db_type = db.get(b"type")
    print(f"type = {db_type.decode()}")

    # 4. Delete -- remove a key
    db.delete(b"license")
    deleted = db.get(b"license")
    print(f"license after delete = {deleted}")

    # 5. Scan -- iterate over all entries (sorted by key)
    print("\nAll entries:")
    for key, value in db:
        print(f"  {key.decode()} => {value.decode()}")

    # 6. Cleanup
    db.close()
    shutil.rmtree(db_path, ignore_errors=True)
    print("\nDone.")


if __name__ == "__main__":
    main()
