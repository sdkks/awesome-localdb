"""
Recipe: Basic KV Store Operations
Database: LMDB
Description: Demonstrates opening an environment, putting, getting, deleting
    keys, and performing a cursor-based iteration.

Usage: python src/recipe_kv_store.py
"""

import os
import shutil
import lmdb


def main():
    db_path = "/tmp/lmdb_recipe_kv_store"

    # 1. Setup — open the environment with a 1 GB map size
    env = lmdb.open(db_path, map_size=1024 * 1024 * 1024, max_dbs=1)

    # 2. Write — insert key-value pairs in a write transaction
    with env.begin(write=True) as txn:
        txn.put(b"name", b"LMDB")
        txn.put(b"type", b"key-value")
        txn.put(b"year", b"2011")
        txn.put(b"license", b"OpenLDAP")

    # 3. Read — retrieve individual keys in a read transaction
    with env.begin() as txn:
        name = txn.get(b"name")
        print(f"name = {name.decode()}")

        db_type = txn.get(b"type")
        print(f"type = {db_type.decode()}")

    # 4. Delete — remove a key in a write transaction
    with env.begin(write=True) as txn:
        txn.delete(b"license")

    with env.begin() as txn:
        deleted = txn.get(b"license")
        print(f"license after delete = {deleted}")

    # 5. Scan — iterate over all entries with a cursor
    print("\nAll entries:")
    with env.begin() as txn:
        with txn.cursor() as cursor:
            for key, value in cursor:
                print(f"  {key.decode()} => {value.decode()}")

    # 6. Cleanup
    env.close()
    shutil.rmtree(db_path, ignore_errors=True)
    print("\nDone.")


if __name__ == "__main__":
    main()
