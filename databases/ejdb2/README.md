# EJDB2

> **Category:** Document | **License:** MIT | **Stars:** ~1,500

## Overview

EJDB2 is an embeddable JSON database engine written in C. It stores BSON documents in a single file powered by the IOWOW key/value storage engine. Its XPath-inspired query language (JQL) supports collection joins, projections, sorting, and in-place data modification. EJDB2 is designed for embedding into applications where a full server-based database would be overkill -- desktop apps, IoT devices, CLI tools, and edge deployments.

## Quick Start

### Python

EJDB2 is a C library with no official pip package. The Python recipe uses `ctypes` to interface with the compiled library. Build EJDB2 from source first, then run:

```python
# Prerequisite: build and install ejdb2 from source
# git clone https://github.com/Softmotions/ejdb && cd ejdb && ./build.sh --prefix=$HOME/.local

import ctypes
import json
import tempfile
import os

# Load the shared library
lib = ctypes.CDLL("libejdb2.so")  # .dylib on macOS, .dll on Windows

# Initialize and open a database
db_path = os.path.join(tempfile.mkdtemp(), "mydb.db")
db = ctypes.c_void_p()
lib.ejdb_open(ctypes.c_char_p(db_path.encode()), ctypes.byref(db))

# Insert a document
from ctypes import c_char_p, c_int64
doc = json.dumps({"name": "Alice", "age": 30})
doc_id = c_int64()
lib.ejdb_put_new(db, c_char_p(b"users"), c_char_p(doc.encode()), ctypes.byref(doc_id))
print(f"Inserted document with id: {doc_id.value}")

# Query with JQL
# ... query execution via the JQL API ...

# Clean up
lib.ejdb_close(ctypes.byref(db))
```

### Go

Use CGo to call the ejdb2 C library directly:

```go
// Build ejdb2 from source first, then:
// CGO_LDFLAGS="-lejdb2" go run main.go

package main

/*
#cgo LDFLAGS: -lejdb2
#include <ejdb2.h>
#include <jbl.h>
#include <jql.h>
*/
import "C"
import "fmt"

func main() {
    // Initialize
    C.ejdb_init()

    // Open database
    opts := C.EJDB_OPTS{
        kv: C.IWKV_OPTS{
            path: C.CString("mydb.db"),
        },
    }
    var db *C.EJDB
    C.ejdb_open(&opts, &db)

    // Insert a document
    var jbl *C.JBL
    C.jbl_from_json(&jbl, C.CString(`{"name":"Alice","age":30}`))
    var id C.int64_t
    C.ejdb_put_new(db, C.CString("users"), jbl, &id)
    fmt.Printf("Inserted document with id: %d\n", id)

    // Execute a JQL query
    var q *C.JQL
    C.jql_create(&q, C.CString("users"), C.CString("/[age > :age]"))
    C.jql_set_i64(q, C.CString("age"), 0, C.int64_t(20))

    // Execute and visit results...

    // Clean up
    C.jql_destroy(&q)
    C.jbl_destroy(&jbl)
    C.ejdb_close(&db)
}
```

## On-Disk Format

Single file (IOWOW key/value storage engine with BSON documents)

## Core Strengths

- XPath-inspired JQL query language with joins, projections, and sorting
- Single-file embedded database with zero configuration required
- Online backups support without stopping the database
- Optional HTTP/WebSocket REST endpoint for network access
- ACID-compliant with indexes on JSON fields for fast queries
- Compact C11 implementation suitable for IoT and edge devices

## Best Use Cases

1. **Embedded JSON Storage** -- Persist structured documents in desktop, CLI, and mobile apps without an external database server.
2. **IoT and Edge Devices** -- Run a full-featured document database on resource-constrained hardware with minimal footprint.
3. **Mobile Applications** -- Use Swift or Kotlin bindings for local on-device storage with JSON-native querying.
4. **Microservices and Prototypes** -- Get a lightweight document store with join support without deploying MongoDB or similar.
5. **Applications Needing Structured Querying** -- Leverage JQL's XPath-like syntax for complex nested JSON queries that simple key/value stores cannot handle.

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| Python | [`recipe_document_store.py`](python/src/recipe_document_store.py) | Document CRUD operations via ctypes |
| Python | [`recipe_json_queries.py`](python/src/recipe_json_queries.py) | JQL querying with filters, projections, and updates |

## Limitations & Caveats

- The C library must be compiled from source; no pre-built binaries are distributed officially.
- Python and Go require native compilation toolchains -- not a pure pip/go get install.
- The JQL query language uses a custom syntax distinct from SQL or MongoDB, which requires learning.
- Concurrent write access is serialized through a file lock; not suitable for high-write-concurrency workloads.
- Node.js bindings have known issues with Node 18+ stream handling in some configurations.
- The issues tracker on GitHub is disabled; community contributions via pull requests only.

## Further Reading

- [Official Documentation & README](https://github.com/Softmotions/ejdb)
- [Source Repository](https://github.com/Softmotions/ejdb)
- [The Story of EJDB 2.0 (Medium)](https://medium.com/@adamansky/ejdb2-41670e80897c)
- [Node.js Binding (npm)](https://www.npmjs.com/package/ejdb2_node)
- [Swift Binding (iOS)](https://github.com/Softmotions/EJDB2Swift)
