"""Tests for recipe_batch_operations.py"""

import os
import shutil
import plyvel
import pytest

from src.recipe_batch_operations import main as run_recipe


def test_recipe_runs_without_error():
    """The recipe should execute without raising an exception."""
    run_recipe()


def test_write_batch_atomic():
    """Verify WriteBatch commits puts and deletes atomically."""
    db_path = "/tmp/leveldb_test_batch"

    try:
        db = plyvel.DB(db_path, create_if_missing=True)

        wb = db.write_batch()
        wb.put(b"batch:1", b"v1")
        wb.put(b"batch:2", b"v2")
        wb.put(b"batch:3", b"v3")
        wb.delete(b"batch:2")
        wb.write()

        assert db.get(b"batch:1") == b"v1"
        assert db.get(b"batch:2") is None
        assert db.get(b"batch:3") == b"v3"

        db.close()
    finally:
        shutil.rmtree(db_path, ignore_errors=True)


def test_write_batch_large_count():
    """Verify a WriteBatch with many entries works correctly."""
    db_path = "/tmp/leveldb_test_batch_large"

    try:
        db = plyvel.DB(db_path, create_if_missing=True)

        wb = db.write_batch()
        count = 100
        for i in range(count):
            wb.put(f"key:{i:04d}".encode(), f"val:{i:04d}".encode())
        wb.write()

        for i in range(count):
            expected = f"val:{i:04d}".encode()
            assert db.get(f"key:{i:04d}".encode()) == expected

        db.close()
    finally:
        shutil.rmtree(db_path, ignore_errors=True)
