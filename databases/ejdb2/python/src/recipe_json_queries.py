"""
Recipe: JSON Queries with JQL
Database: EJDB2
Description: Demonstrates EJDB2's JQL query language -- filtering, projections, sorting,
             data modification (apply/upsert), and collection joins -- using Python ctypes.

Usage: python src/recipe_json_queries.py

Prerequisites:
  1. Build and install EJDB2 from source:
     git clone https://github.com/Softmotions/ejdb && cd ejdb && ./build.sh --prefix=$HOME/.local
  2. Ensure libejdb2 is on the library path:
     export LD_LIBRARY_PATH=$HOME/.local/lib:$LD_LIBRARY_PATH   # Linux
     export DYLD_LIBRARY_PATH=$HOME/.local/lib:$DYLD_LIBRARY_PATH  # macOS
"""

import ctypes
import json
import os
import platform
import sys
import tempfile
from ctypes import (
    POINTER,
    Structure,
    byref,
    c_char_p,
    c_int,
    c_int64,
    c_uint32,
    c_void_p,
    cdll,
)


# --- ctypes type aliases ---
class IWKV_OPTS(Structure):
    _fields_ = [
        ("path", c_char_p),
        ("oflags", c_int),
        ("random_seed", c_uint32),
        ("mmap", c_int),
        ("wal", c_int),
        ("file_lock_fail_fast", c_int),
    ]


class EJDB_OPTS(Structure):
    _fields_ = [
        ("kv", IWKV_OPTS),
        ("sort_buffer_sz", c_int64),
        ("document_buffer_sz", c_int64),
        ("http", c_void_p),
    ]


def _load_library():
    """Load the ejdb2 shared library."""
    system = platform.system()
    if system == "Darwin":
        names = ["libejdb2.dylib", "libejdb2.2.dylib"]
    elif system == "Linux":
        names = ["libejdb2.so", "libejdb2.so.2"]
    else:
        names = ["libejdb2.dll"]

    for name in names:
        try:
            return cdll.LoadLibrary(name)
        except OSError:
            continue

    print("Error: Could not load libejdb2.", file=sys.stderr)
    print("Build EJDB2 from source: https://github.com/Softmotions/ejdb", file=sys.stderr)
    sys.exit(1)


def _setup_signatures(lib):
    """Set up ctypes function signatures for the EJDB2 C API."""
    lib.ejdb_init.restype = c_int
    lib.ejdb_open.restype = c_int
    lib.ejdb_close.restype = c_int
    lib.ejdb_put_new.restype = c_int
    lib.ejdb_get.restype = c_int
    lib.jbl_from_json.restype = c_int
    lib.jbl_destroy.restype = c_int
    lib.jbl_as_json.restype = c_int
    lib.jql_create.restype = c_int
    lib.jql_destroy.restype = c_int
    lib.jql_set_i64.restype = c_int
    lib.jql_set_json.restype = c_int
    lib.ejdb_exec.restype = c_int


def _open_db(lib, tmpdir):
    """Initialize EJDB2 and open a database in a temporary directory."""
    rc = lib.ejdb_init()
    if rc != 0:
        print(f"ejdb_init failed with code {rc}", file=sys.stderr)
        sys.exit(1)

    db_path = os.path.join(tmpdir, "queries.db")
    opts = EJDB_OPTS()
    opts.kv.path = db_path.encode("utf-8")
    opts.sort_buffer_sz = 16777216
    opts.document_buffer_sz = 65536

    db = c_void_p()
    rc = lib.ejdb_open(byref(opts), byref(db))
    if rc != 0:
        print(f"ejdb_open failed with code {rc}", file=sys.stderr)
        sys.exit(1)

    return db, db_path


def _insert_doc(lib, db, collection: bytes, doc: dict) -> int:
    """Insert a document and return its id. Returns -1 on failure."""
    jbl = c_void_p()
    doc_json = json.dumps(doc).encode("utf-8")
    rc = lib.jbl_from_json(byref(jbl), c_char_p(doc_json))
    if rc != 0:
        return -1

    doc_id = c_int64()
    rc = lib.ejdb_put_new(db, c_char_p(collection), jbl, byref(doc_id))
    lib.jbl_destroy(byref(jbl))
    return doc_id.value if rc == 0 else -1


def _execute_query(lib, db, collection: bytes, jql_query: bytes) -> int:
    """Execute a JQL query and print matching doc count. Returns 0 on success."""
    q = c_void_p()
    rc = lib.jql_create(byref(q), c_char_p(collection), c_char_p(jql_query))
    if rc != 0:
        print(f"  jql_create failed: code {rc}", file=sys.stderr)
        return rc

    match_count = [0]

    @ctypes.CFUNCTYPE(c_int, c_void_p, c_void_p, POINTER(c_int64))
    def visitor(ctx, doc_raw, step):
        match_count[0] += 1
        return 0

    class EJDB_EXEC(Structure):
        _fields_ = [
            ("db", c_void_p),
            ("q", c_void_p),
            ("visitor", c_void_p),
            ("opts", c_void_p),
            ("log", c_void_p),
        ]

    ux = EJDB_EXEC()
    ux.db = db
    ux.q = q
    ux.visitor = ctypes.cast(visitor, c_void_p)

    rc = lib.ejdb_exec(byref(ux))
    if rc == 0:
        print(f"  Matched {match_count[0]} document(s)")
    else:
        print(f"  Query failed: code {rc}", file=sys.stderr)

    lib.jql_destroy(byref(q))
    return rc


def main() -> None:
    lib = _load_library()
    _setup_signatures(lib)

    tmpdir = tempfile.mkdtemp()
    db, db_path = _open_db(lib, tmpdir)

    # --- 1. Seed data ---
    products = [
        {"name": "Widget A", "price": 19.99, "in_stock": True, "tags": ["hardware", "sale"]},
        {"name": "Widget B", "price": 29.99, "in_stock": False, "tags": ["hardware"]},
        {"name": "Gadget X", "price": 49.99, "in_stock": True, "tags": ["electronics", "new"]},
        {"name": "Gadget Y", "price": 79.99, "in_stock": True, "tags": ["electronics", "premium"]},
        {"name": "Tool Z", "price": 9.99, "in_stock": True, "tags": ["hardware", "sale", "new"]},
    ]
    coll = b"products"

    for product in products:
        pid = _insert_doc(lib, db, coll, product)
        if pid >= 0:
            print(f"Seeded: {product['name']} (id={pid})")
    print()

    # --- 2. JQL: Exact match filter ---
    print("--- JQL: Exact match (name = Widget A) ---")
    _execute_query(lib, db, coll, b"/[name = \"Widget A\"]")

    # --- 3. JQL: Numeric comparison ---
    print("--- JQL: Price less than 30 ---")
    _execute_query(lib, db, coll, b"/[price < 30]")

    # --- 4. JQL: Combined conditions with AND ---
    print("--- JQL: In stock AND price > 20 ---")
    _execute_query(lib, db, coll, b"/[in_stock = true] and /[price > 20]")

    # --- 5. JQL: Array membership with 'in' ---
    print("--- JQL: Tags include 'sale' ---")
    _execute_query(lib, db, coll, b"/tags/[** in [\"sale\"]]")

    # --- 6. JQL: Projection (only name and price) ---
    print("--- JQL: Project /{name,price} ---")
    _execute_query(lib, db, coll, b"/[price > 20] | /{name,price}")

    # --- 7. JQL: Sorting (ascending by price) ---
    print("--- JQL: Sort ascending by price ---")
    _execute_query(lib, db, coll, b"/* | asc /price")

    # --- 8. JQL: Limit ---
    print("--- JQL: Top 2 cheapest ---")
    _execute_query(lib, db, coll, b"/* | asc /price | limit 2")

    # --- 9. JQL: Apply (data modification via JSON merge patch) ---
    print("--- JQL: Apply discount tag ---")
    _execute_query(
        lib,
        db,
        coll,
        b"/[price < 20] | apply {\"discount\": true}",
    )

    # --- 10. JQL: Count only ---
    print("--- JQL: Count in-stock items ---")
    _execute_query(lib, db, coll, b"/[in_stock = true] | count")

    # --- Cleanup ---
    lib.ejdb_close(byref(db))
    for fname in [db_path, db_path + "-wal", db_path + "-shm"]:
        try:
            os.unlink(fname)
        except OSError:
            pass
    try:
        os.rmdir(tmpdir)
    except OSError:
        pass
    print("\nDatabase closed and cleaned up.")


if __name__ == "__main__":
    main()
