"""Tests for recipe_kv_store.py"""

import os
import shutil
import lmdb

from src.recipe_kv_store import main as run_recipe


def test_recipe_runs_without_error():
    """The recipe should execute without raising an exception."""
    run_recipe()


def test_kv_store_operations():
    """Verify basic put, get, delete operations work correctly."""
    db_path = "/tmp/lmdb_test_kv_store"

    try:
        env = lmdb.open(db_path, map_size=1024 * 1024 * 1024, max_dbs=1)

        with env.begin(write=True) as txn:
            txn.put(b"test_key", b"test_value")

        with env.begin() as txn:
            assert txn.get(b"test_key") == b"test_value"

        with env.begin(write=True) as txn:
            txn.delete(b"test_key")

        with env.begin() as txn:
            assert txn.get(b"test_key") is None

        env.close()
    finally:
        shutil.rmtree(db_path, ignore_errors=True)


def test_cursor_iteration():
    """Verify cursor can iterate all entries in sorted key order."""
    db_path = "/tmp/lmdb_test_cursor"

    try:
        env = lmdb.open(db_path, map_size=1024 * 1024 * 1024, max_dbs=1)

        with env.begin(write=True) as txn:
            txn.put(b"c", b"3")
            txn.put(b"a", b"1")
            txn.put(b"b", b"2")

        with env.begin() as txn:
            with txn.cursor() as cursor:
                results = list(cursor)

        assert len(results) == 3
        # LMDB returns keys in lexicographic order
        assert results[0] == (b"a", b"1")
        assert results[1] == (b"b", b"2")
        assert results[2] == (b"c", b"3")

        env.close()
    finally:
        shutil.rmtree(db_path, ignore_errors=True)
