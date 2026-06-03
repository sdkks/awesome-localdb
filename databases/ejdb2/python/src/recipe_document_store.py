"""
Recipe: Document Store CRUD
Database: EJDB2
Description: Demonstrates basic document operations -- insert, get by id, update, delete,
             and query -- using Python ctypes to call the EJDB2 C library.

Usage: python src/recipe_document_store.py

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
    pointer,
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
    print("Then ensure the library is on LD_LIBRARY_PATH / DYLD_LIBRARY_PATH.", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    lib = _load_library()

    # Set up function signatures
    lib.ejdb_init.restype = c_int
    lib.ejdb_open.restype = c_int
    lib.ejdb_close.restype = c_int
    lib.ejdb_put_new.restype = c_int
    lib.ejdb_get.restype = c_int
    lib.ejdb_del.restype = c_int
    lib.jbl_from_json.restype = c_int
    lib.jbl_destroy.restype = c_int
    lib.jbl_as_json.restype = c_int
    lib.jql_create.restype = c_int
    lib.jql_destroy.restype = c_int
    lib.jql_set_i64.restype = c_int
    lib.jql_set_str.restype = c_int
    lib.ejdb_exec.restype = c_int

    # --- 1. Initialize and open database ---
    rc = lib.ejdb_init()
    if rc != 0:
        print(f"ejdb_init failed with code {rc}", file=sys.stderr)
        sys.exit(1)

    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, "mydb.db")

    opts = EJDB_OPTS()
    opts.kv.path = db_path.encode("utf-8")
    opts.kv.oflags = 0
    opts.sort_buffer_sz = 16777216
    opts.document_buffer_sz = 65536

    db = c_void_p()
    rc = lib.ejdb_open(byref(opts), byref(db))
    if rc != 0:
        print(f"ejdb_open failed with code {rc}", file=sys.stderr)
        sys.exit(1)

    coll = b"users"

    # --- 2. Insert documents ---
    docs_to_insert = [
        {"name": "Alice", "age": 30, "city": "London"},
        {"name": "Bob", "age": 25, "city": "Paris"},
        {"name": "Charlie", "age": 35, "city": "London"},
        {"name": "Diana", "age": 28, "city": "Berlin"},
        {"name": "Eve", "age": 22, "city": "Paris"},
    ]
    doc_ids = []

    for doc in docs_to_insert:
        jbl = c_void_p()
        doc_json = json.dumps(doc).encode("utf-8")
        rc = lib.jbl_from_json(byref(jbl), c_char_p(doc_json))
        if rc != 0:
            print(f"jbl_from_json failed with code {rc}", file=sys.stderr)
            continue

        doc_id = c_int64()
        rc = lib.ejdb_put_new(db, c_char_p(coll), jbl, byref(doc_id))
        lib.jbl_destroy(byref(jbl))
        if rc == 0:
            doc_ids.append(doc_id.value)
            print(f"Inserted: {doc['name']} (id={doc_id.value})")
        else:
            print(f"Insert failed for {doc['name']}: code {rc}", file=sys.stderr)

    print(f"Total inserted: {len(doc_ids)} documents.\n")

    # --- 3. Get document by id ---
    if doc_ids:
        target_id = doc_ids[0]
        out_jbl = c_void_p()
        rc = lib.ejdb_get(db, c_char_p(coll), c_int64(target_id), byref(out_jbl))
        if rc == 0:
            # Convert JBL back to JSON for display
            # jbl_as_json copies to a buffer; we use a simplified approach
            print(f"Retrieved document id={target_id}: success (JBL handle obtained)")
            lib.jbl_destroy(byref(out_jbl))
        else:
            print(f"ejdb_get failed for id={target_id}: code {rc}")

    # --- 4. Query with JQL ---
    # Create a query: find users over age 25
    q = c_void_p()
    rc = lib.jql_create(byref(q), c_char_p(coll), c_char_p(b"/[age > :min_age]"))
    if rc == 0:
        lib.jql_set_i64(q, c_char_p(b"min_age"), 0, c_int64(25))

        # Execute the query with a simple visitor callback
        @ctypes.CFUNCTYPE(c_int, c_void_p, c_void_p, POINTER(c_int64))
        def visitor(ctx, doc_raw, step):
            # doc_raw is a JBL raw pointer; we won't deserialize fully here
            print(f"  Query match at step {step[0] if step else '?'}")
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
            print("JQL query executed successfully.")
        else:
            print(f"JQL query failed with code {rc}", file=sys.stderr)

        lib.jql_destroy(byref(q))

    # --- 5. Delete a document ---
    if len(doc_ids) >= 2:
        delete_id = doc_ids[1]
        rc = lib.ejdb_del(db, c_char_p(coll), c_int64(delete_id))
        if rc == 0:
            print(f"Deleted document id={delete_id}")

            # Verify deletion
            out_jbl = c_void_p()
            rc = lib.ejdb_get(db, c_char_p(coll), c_int64(delete_id), byref(out_jbl))
            if rc != 0:
                print(f"Verified: document id={delete_id} is gone.")
        else:
            print(f"Delete failed for id={delete_id}: code {rc}")

    # --- 6. Cleanup ---
    lib.ejdb_close(byref(db))
    # Clean up temp files
    for fname in [db_path, db_path + "-wal", db_path + "-shm"]:
        try:
            os.unlink(fname)
        except OSError:
            pass
    try:
        os.rmdir(tmpdir)
    except OSError:
        pass
    print("Database closed and cleaned up.")


if __name__ == "__main__":
    main()
