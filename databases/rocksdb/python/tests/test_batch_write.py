"""Tests for recipe_batch_write.py"""

import os
import shutil
import rocksdbpy
import pytest

from src.recipe_batch_write import main as run_recipe


def test_recipe_runs_without_error():
    """The recipe should execute without raising an exception."""
    run_recipe()


def test_write_batch_atomic():
    """Verify WriteBatch commits puts and deletes atomically."""
    db_path = "/tmp/rocksdb_test_batch"

    try:
        db = rocksdbpy.open_default(db_path)

        batch = rocksdbpy.WriteBatch()
        batch.add(b"batch:1", b"v1")
        batch.add(b"batch:2", b"v2")
        batch.add(b"batch:3", b"v3")
        batch.delete(b"batch:2")
        db.write(batch)

        assert db.get(b"batch:1") == b"v1"
        assert db.get(b"batch:2") is None
        assert db.get(b"batch:3") == b"v3"

        db.close()
    finally:
        shutil.rmtree(db_path, ignore_errors=True)


def test_write_batch_large_count():
    """Verify a WriteBatch with many entries works correctly."""
    db_path = "/tmp/rocksdb_test_batch_large"

    try:
        db = rocksdbpy.open_default(db_path)

        batch = rocksdbpy.WriteBatch()
        count = 100
        for i in range(count):
            batch.add(f"key:{i:04d}".encode(), f"val:{i:04d}".encode())
        db.write(batch)

        for i in range(count):
            expected = f"val:{i:04d}".encode()
            assert db.get(f"key:{i:04d}".encode()) == expected

        db.close()
    finally:
        shutil.rmtree(db_path, ignore_errors=True)
