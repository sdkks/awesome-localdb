# ArcadeDB

> **Category:** multi-model | **License:** Apache-2.0 | **Stars:** ~900

## Overview

ArcadeDB is a multi-model database that natively supports graphs, documents, key-value, vectors, full-text search, and time-series in a single engine with ACID transactions. It runs embedded inside Java (JVM) and Python applications -- the Python `arcadedb-embedded` package bundles a Java runtime with the wheel for zero-dependency use. ArcadeDB supports SQL, OpenCypher (97.8% TCK compatibility), Gremlin, GraphQL, and MongoDB query language. Created by the founder of OrientDB, ArcadeDB is Apache 2.0 forever.

## Quick Start

### Python

```python
# Install: pip install arcadedb-embedded
import arcadedb_embedded as arcadedb

# Open or create a database (context-managed)
with arcadedb.create_database("./mydb") as db:
    with db.transaction():
        # Define schema
        db.command("sql", "CREATE VERTEX TYPE Person")
        db.command("sql", "CREATE EDGE TYPE Knows")

        # Create vertices
        db.command("sql",
            "INSERT INTO Person SET name = 'Alice', age = 32")
        db.command("sql",
            "INSERT INTO Person SET name = 'Bob', age = 28")

        # Create edge
        db.command("sql",
            "CREATE EDGE Knows "
            "FROM (SELECT FROM Person WHERE name='Alice') "
            "TO (SELECT FROM Person WHERE name='Bob') "
            "SET since = 2020")

    # Query with SQL
    result = db.query("sql", "SELECT FROM Person WHERE age > 25")
    for row in result:
        print(row.get("name"), row.get("age"))

    # Query with OpenCypher
    result = db.query("cypher",
        "MATCH (p:Person)-[:Knows]->(f) "
        "WHERE p.name = 'Alice' "
        "RETURN f.name, f.age")
    for row in result:
        print(row.get("name"), row.get("age"))
```

### Java

```java
// Maven: com.arcadedb:arcadedb-engine:26.5.1
import com.arcadedb.database.Database;
import com.arcadedb.database.DatabaseFactory;
import com.arcadedb.graph.Vertex;

try (Database db = new DatabaseFactory("/data/mydb").create()) {
    db.transaction(tx -> {
        db.getSchema().createVertexType("Person");
        db.getSchema().createEdgeType("Knows");

        Vertex alice = db.newVertex("Person")
            .set("name", "Alice").set("age", 32).save();
        Vertex bob = db.newVertex("Person")
            .set("name", "Bob").set("age", 28).save();

        alice.newEdge("Knows", bob, true)
            .set("since", 2020).save();
    });

    // Query with SQL
    db.query("sql",
        "SELECT FROM Person WHERE age > ?", 25);
}
```

## On-Disk Format

Multi-file (WAL journal + LSM-Tree indexes + columnar time-series chunks). ArcadeDB stores data across multiple files in a directory: a write-ahead log for crash recovery, LSM-tree based index files for vertices/edges/documents, and columnar-encoded chunks for time-series data. Supports both persistent file-based storage and in-memory mode.

## Core Strengths

- Five data models in one engine: graph, document, key-value, vector, time-series
- Embedded Python via `pip install arcadedb-embedded` with bundled JRE, zero Java setup
- Native OpenCypher 25 support passing 97.8% of official TCK
- JVector-powered vector search with HNSW+DiskANN hybrid and SIMD acceleration
- ACID transactions with WAL crash recovery and MVCC concurrency control
- Same engine runs embedded, single-node server, or Raft-replicated HA cluster

## Best Use Cases

1. **GraphRAG and AI pipelines** -- Combine vector similarity search with graph relationship traversal in a single in-process query
2. **Local-first apps needing multi-model storage** -- Document, graph, and vector models in one embedded database with zero external services
3. **Data science notebooks** -- Persistent multi-model storage between kernel restarts, mix graph queries with pandas/numpy
4. **Edge/IoT devices** -- Process sensor time-series alongside graph device topologies on resource-constrained hardware
5. **Desktop and CLI tools** -- Ship a full database engine as part of your application with no separate install

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| Python | [`recipe_multi_model.py`](python/src/recipe_multi_model.py) | Multi-model demo: graph vertices+edges, document CRUD, vector index, time-series |

## Limitations & Caveats

- Python embedded mode bundles a Java 25 JRE via JPype; first import initializes the JVM (~1-2s startup)
- The `arcadedb-embedded` wheel is ~73 MB due to the bundled JRE
- Not all query languages available from Python -- Gremlin and GraphQL are Java-only
- HA replication requires running the embedded server, not pure embedded mode
- GraphOLTP focus; not designed for analytical/OLAP workloads (use DuckDB for that)

## Further Reading

- [Official Documentation](https://docs.arcadedb.com)
- [Source Repository](https://github.com/ArcadeData/arcadedb)
- [Python Embedded Guide](https://arcadedb.com/python-embedded.html)
- [Java Embedded Guide](https://arcadedb.com/embedded.html)
