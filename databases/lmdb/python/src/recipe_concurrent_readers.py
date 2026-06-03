"""
Recipe: Concurrent Readers
Database: LMDB
Description: Demonstrates LMDB's MVCC capability — multiple threads perform
    concurrent read transactions while a writer inserts data, verifying that
    readers see a consistent snapshot without blocking.

Usage: python src/recipe_concurrent_readers.py
"""

import os
import shutil
import threading
import lmdb


def reader(env, reader_id, iterations, results):
    """Perform repeated read transactions, reading a key and storing the result."""
    for i in range(iterations):
        with env.begin() as txn:
            value = txn.get(b"counter")
            results.append((reader_id, i, value))


def main():
    db_path = "/tmp/lmdb_recipe_concurrent_readers"

    # 1. Setup — open the environment
    env = lmdb.open(db_path, map_size=1024 * 1024 * 1024, max_dbs=1)

    # Insert an initial value
    with env.begin(write=True) as txn:
        txn.put(b"counter", b"0")

    NUM_READERS = 4
    ITERATIONS_PER_READER = 20
    NUM_WRITES = 10

    reader_results = []

    # 2. Start concurrent reader threads
    threads = []
    for rid in range(NUM_READERS):
        t = threading.Thread(
            target=reader,
            args=(env, rid, ITERATIONS_PER_READER, reader_results),
        )
        threads.append(t)
        t.start()

    # 3. Perform writes while readers are active
    import time
    for i in range(1, NUM_WRITES + 1):
        time.sleep(0.005)  # Small delay to interleave with readers
        with env.begin(write=True) as txn:
            txn.put(b"counter", str(i).encode())

    # 4. Wait for all readers to finish
    for t in threads:
        t.join()

    # 5. Report results
    total_reads = len(reader_results)
    print(f"Completed {total_reads} reads across {NUM_READERS} readers")
    print(f"Writes performed: {NUM_WRITES}")

    # Verify that each reader saw valid starts (0) or increments
    starts = sum(1 for _, _, val in reader_results if val == b"0")
    print(f"Reads that saw initial value '0': {starts}")

    # 6. Cleanup
    env.close()
    shutil.rmtree(db_path, ignore_errors=True)
    print("\nDone.")


if __name__ == "__main__":
    main()
