"""Tests for recipe_kv_store.py"""

import asyncio
import tempfile
from pathlib import Path

import pytest
from slatedb.uniffi._slatedb_uniffi import DbBuilder, KeyRange, ObjectStore

from src.recipe_kv_store import main


@pytest.mark.asyncio
async def test_recipe_runs_without_error():
    """The recipe should execute without raising an exception."""
    await main()


@pytest.mark.asyncio
async def test_open_put_get_delete():
    """Verify basic open, put, get, and delete operations."""
    tmpdir = tempfile.mkdtemp(prefix="slatedb_test_")
    store = ObjectStore.resolve(f"file://{tmpdir}")
    builder = DbBuilder("/test-db", store)
    db = await builder.build()

    # Put and get
    await db.put(b"hello", b"world")
    value = await db.get(b"hello")
    assert value == b"world"

    # Put another key
    await db.put(b"count", b"42")
    value = await db.get(b"count")
    assert value == b"42"

    # Get non-existent key
    missing = await db.get(b"nope")
    assert missing is None

    # Delete
    await db.delete(b"hello")
    value = await db.get(b"hello")
    assert value is None

    await db.shutdown()
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.mark.asyncio
async def test_list_keys():
    """Verify listing keys returns expected entries."""
    tmpdir = tempfile.mkdtemp(prefix="slatedb_test_")
    store = ObjectStore.resolve(f"file://{tmpdir}")
    builder = DbBuilder("/list-db", store)
    db = await builder.build()

    await db.put(b"a", b"1")
    await db.put(b"b", b"2")
    await db.put(b"c", b"3")

    key_range = KeyRange(start=None, start_inclusive=False, end=None, end_inclusive=False)
    iterator = await db.scan(key_range)
    keys = []
    while (kv := await iterator.next()) is not None:
        keys.append(kv.key)

    assert b"a" in keys
    assert b"b" in keys
    assert b"c" in keys

    await db.shutdown()
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)
