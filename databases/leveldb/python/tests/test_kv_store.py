"""Tests for recipe_kv_store.py"""

import os
import shutil
import plyvel
import pytest

from src.recipe_kv_store import main as run_recipe


def test_recipe_runs_without_error():
    """The recipe should execute without raising an exception."""
    run_recipe()


def test_kv_store_operations():
    """Verify basic put, get, delete operations work correctly."""
    db_path = "/tmp/leveldb_test_kv_store"

    try:
        db = plyvel.DB(db_path, create_if_missing=True)

        db.put(b"test_key", b"test_value")
        assert db.get(b"test_key") == b"test_value"

        db.delete(b"test_key")
        assert db.get(b"test_key") is None

        db.close()
    finally:
        shutil.rmtree(db_path, ignore_errors=True)


def test_get_default():
    """Verify get returns a default value when key is missing."""
    db_path = "/tmp/leveldb_test_default"

    try:
        db = plyvel.DB(db_path, create_if_missing=True)

        result = db.get(b"nonexistent", b"fallback")
        assert result == b"fallback"

        db.close()
    finally:
        shutil.rmtree(db_path, ignore_errors=True)


def test_iterator_scan():
    """Verify iterator can scan all entries in sorted key order."""
    db_path = "/tmp/leveldb_test_iterator"

    try:
        db = plyvel.DB(db_path, create_if_missing=True)

        db.put(b"c", b"3")
        db.put(b"a", b"1")
        db.put(b"b", b"2")

        results = []
        for key, value in db:
            results.append((key, value))

        assert len(results) == 3
        assert results[0] == (b"a", b"1")
        assert results[1] == (b"b", b"2")
        assert results[2] == (b"c", b"3")

        db.close()
    finally:
        shutil.rmtree(db_path, ignore_errors=True)
