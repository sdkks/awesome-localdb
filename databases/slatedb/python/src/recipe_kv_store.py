"""
Recipe: Basic KV Store Operations
Database: SlateDB
Description: Demonstrates opening a SlateDB database backed by an in-memory
             object store, putting, getting, deleting, and listing keys.

Usage: python src/recipe_kv_store.py
"""

import asyncio
import tempfile
from pathlib import Path

from slatedb.uniffi._slatedb_uniffi import DbBuilder, KeyRange, ObjectStore


async def main():
    # 1. Setup -- create a temporary directory for the local object store
    tmpdir = tempfile.mkdtemp(prefix="slatedb_recipe_")
    store = ObjectStore.resolve(f"file://{tmpdir}")
    builder = DbBuilder("/recipe-db", store)
    db = await builder.build()

    # 2. Write -- insert key-value pairs
    await db.put(b"name", b"SlateDB")
    await db.put(b"type", b"key-value")
    await db.put(b"year", b"2024")
    await db.put(b"license", b"Apache-2.0")
    print("Inserted 4 key-value pairs.")

    # 3. Read -- retrieve individual keys
    name = await db.get(b"name")
    kind = await db.get(b"type")
    print(f"name = {name}")
    print(f"type = {kind}")

    # 4. Delete -- remove a key
    await db.delete(b"license")
    deleted = await db.get(b"license")
    print(f"license (after delete) = {deleted}")

    # 5. List -- iterate over all keys
    print("\nAll entries:")
    key_range = KeyRange(start=None, start_inclusive=False, end=None, end_inclusive=False)
    iterator = await db.scan(key_range)
    while (kv := await iterator.next()) is not None:
        print(f"  {kv.key} => {kv.value}")

    # 6. Cleanup
    await db.shutdown()
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)
    print(f"\nCleaned up {tmpdir}")


if __name__ == "__main__":
    asyncio.run(main())
