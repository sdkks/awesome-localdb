"""Tests for recipe_kv_store.py"""

import os
import shutil
import rocksdbpy
import pytest

from src.recipe_kv_store import main as run_recipe


def test_recipe_runs_without_error():
    """The recipe should execute without raising an exception."""
    run_recipe()


def test_kv_store_operations():
    """Verify basic put, get, delete operations work correctly."""
    db_path = "/tmp/rocksdb_test_kv_store"

    try:
        db = rocksdbpy.open_default(db_path)

        db.set(b"test_key", b"test_value")
        assert db.get(b"test_key") == b"test_value"

        db.delete(b"test_key")
        assert db.get(b"test_key") is None

        db.close()
    finally:
        shutil.rmtree(db_path, ignore_errors=True)


def test_iterator_scan():
    """Verify iterator can scan all entries."""
    db_path = "/tmp/rocksdb_test_iterator"

    try:
        db = rocksdbpy.open_default(db_path)

        db.set(b"a", b"1")
        db.set(b"b", b"2")
        db.set(b"c", b"3")

        results = []
        for key, value in db.iterator():
            results.append((key, value))

        assert len(results) == 3
        assert results[0] == (b"a", b"1")
        assert results[1] == (b"b", b"2")
        assert results[2] == (b"c", b"3")

        db.close()
    finally:
        shutil.rmtree(db_path, ignore_errors=True)
