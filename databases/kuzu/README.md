# Kuzu

> **Category:** Graph | **License:** MIT | **Stars:** ~3.9k

## Overview

Kuzu is an embedded property graph database built for fast analytical queries. It implements the openCypher query language on a columnar storage engine, making it ideal for pattern matching, path traversal, and relationship analytics. With built-in vector search and full-text search, Kuzu handles hybrid graph+semantic workloads entirely in-process with no server required.

## Quick Start

### Python

```python
# Install: pip install kuzu
import kuzu

# Connect / open
db = kuzu.Database("mydb")
conn = kuzu.Connection(db)

# Define schema
conn.execute("CREATE NODE TABLE Person(name STRING, age INT64, PRIMARY KEY (name))")
conn.execute("CREATE REL TABLE Knows(FROM Person TO Person, since INT64)")

# Insert data
conn.execute('CREATE (:Person {name: "Alice", age: 30})')
conn.execute('CREATE (:Person {name: "Bob", age: 25})')
conn.execute('MATCH (a:Person), (b:Person) WHERE a.name = "Alice" AND b.name = "Bob" CREATE (a)-[:Knows {since: 2020}]->(b)')

# Query
results = conn.execute("MATCH (a:Person)-[k:Knows]->(b:Person) RETURN a.name, b.name, k.since")
while results.has_next():
    print(results.get_next())
```

### Rust

```rust
// Cargo.toml: kuzu = "0.11"
use kuzu::{Database, Connection};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let db = Database::new("mydb")?;
    let conn = Connection::new(&db)?;
    // ...
    Ok(())
}
```

### JavaScript

```javascript
// Install: npm install kuzu
const kuzu = require("kuzu");

const db = new kuzu.Database("mydb");
const conn = new kuzu.Connection(db);
// ...
```

## On-Disk Format

Columnar Storage (multi-file: node/rel groups, WAL, catalog)

## Core Strengths

- openCypher query language for expressive graph pattern matching
- Columnar storage engine optimized for analytical graph queries
- Built-in vector similarity search with HNSW index
- Built-in full-text search indexing
- Zero-configuration embedded deployment with no external daemon
- Cross-language client APIs (C++, Python, Rust, JS, Java)

## Best Use Cases

1. **Analytical Graph Queries** -- Run Cypher MATCH patterns with aggregations over large property graph datasets.
2. **Graph-Based Recommendations** -- Traverse relationships and compute graph metrics (PageRank, centrality) for ranking.
3. **Fraud Detection** -- Detect suspicious patterns with complex multi-hop relationship queries.

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| Python | [`recipe_graph_traversal.py`](python/src/recipe_graph_traversal.py) | Create nodes and edges, run Cypher MATCH traversal queries |
| Python | [`recipe_graph_analytics.py`](python/src/recipe_graph_analytics.py) | Compute PageRank iteratively on a graph stored in Kuzu |

## Limitations & Caveats

- Kuzu is optimized for analytical (read-heavy) workloads, not high-throughput transactional writes.
- The columnar on-disk format uses multiple files; not suited for single-file portability.
- Writes are serialized through a single-writer model; concurrent writes are not supported.
- No built-in graph algorithm library (PageRank, community detection must be implemented in application code).

## Further Reading

- [Official Documentation](https://docs.kuzudb.com)
- [Source Repository](https://github.com/kuzudb/kuzu)
