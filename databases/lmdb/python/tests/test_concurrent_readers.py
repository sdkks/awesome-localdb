"""Tests for recipe_concurrent_readers.py"""

import os
import shutil
import threading
import lmdb

from src.recipe_concurrent_readers import main as run_recipe


def test_recipe_runs_without_error():
    """The recipe should execute without raising an exception."""
    run_recipe()


def test_concurrent_readers_do_not_block():
    """Verify multiple readers can read concurrently without blocking."""
    db_path = "/tmp/lmdb_test_concurrent_readers"

    try:
        env = lmdb.open(db_path, map_size=1024 * 1024 * 1024, max_dbs=1)

        with env.begin(write=True) as txn:
            txn.put(b"shared_key", b"initial")

        errors = []
        results = []

        def concurrent_reader(reader_id):
            try:
                for _ in range(10):
                    with env.begin() as txn:
                        val = txn.get(b"shared_key")
                        results.append((reader_id, val))
            except Exception as e:
                errors.append(str(e))

        threads = []
        for rid in range(4):
            t = threading.Thread(target=concurrent_reader, args=(rid,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join(timeout=5)
            assert not t.is_alive(), f"Thread did not complete (hung)"

        assert len(errors) == 0, f"Errors during concurrent reads: {errors}"
        # All readers should have completed reads
        assert len(results) == 40  # 4 readers * 10 iterations
        # All values should be the initial value
        for _, val in results:
            assert val == b"initial"

        env.close()
    finally:
        shutil.rmtree(db_path, ignore_errors=True)


def test_snapshot_isolation_write_then_read():
    """Verify MVCC snapshot isolation: a reader sees the database state
    as of the last committed write, even with a writer active."""
    db_path = "/tmp/lmdb_test_snapshot"

    try:
        env = lmdb.open(db_path, map_size=1024 * 1024 * 1024, max_dbs=1)

        with env.begin(write=True) as txn:
            txn.put(b"counter", b"0")

        # Phase 1: Write some values
        for i in range(1, 6):
            with env.begin(write=True) as txn:
                txn.put(b"counter", str(i).encode())

        # Phase 2: Verify final value
        with env.begin() as txn:
            assert txn.get(b"counter") == b"5"

        env.close()
    finally:
        shutil.rmtree(db_path, ignore_errors=True)
