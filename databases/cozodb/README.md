# CozoDB

> **Category:** Graph | **License:** MPL-2.0 | **Stars:** ~4k

## Overview

CozoDB is a general-purpose, transactional database that uses Datalog (CozoScript) as its query language. It focuses on graph data and algorithms, with built-in support for time-travel queries, vector similarity search, and recursive deductive reasoning. CozoDB runs embedded in Rust and Python via SQLite or RocksDB backends, yet can also operate as a standalone server for distributed deployments.

## Quick Start

### Python

```python
# Install: pip install "pycozo[embedded]"
from pycozo.client import Client

# Connect / open (in-memory)
client = Client()

# Or persistent: client = Client('sqlite', 'mydb.db')

# Define a relation and insert data
client.run(":create friend {name: String, best_friend: String}")
client.run("?[name, best_friend] <- [['Alice', 'Bob'], ['Bob', 'Carol'], ['Carol', 'Dan']] :put friend {name, best_friend}")

# Query with a Datalog rule
res = client.run("?[a, b] := *friend[a, b]")
print(res['rows'])
# [['Alice', 'Bob'], ['Bob', 'Carol'], ['Carol', 'Dan']]

# Recursive query: find all friends-of-friends
res = client.run("""
  reachable[a, b] := *friend[a, b]
  reachable[a, c] := *friend[a, b], reachable[b, c]
  ?[a, b] := reachable[a, b]
""")
print(res['rows'])
# [['Alice', 'Bob'], ['Alice', 'Carol'], ['Alice', 'Dan'], ...]

client.close()
```

### Rust

```rust
// Cargo.toml: cozo = "0.7"
use cozo::Db;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let db = Db::new("sqlite", "mydb.db", Default::default())?;
    // ...
    Ok(())
}
```

## On-Disk Format

SQLite-backed (single-file) or RocksDB LSMT (multi-file); also in-memory

## Core Strengths

- Datalog (CozoScript) query language with recursive rules and deductive reasoning
- Built-in graph algorithms: shortest path, PageRank, community detection, centrality
- Time-travel queries: query historical snapshots of data at any point in time
- Embedded mode with zero dependencies via SQLite or RocksDB storage backends
- Vector similarity search natively integrated into the Datalog engine
- Multi-statement transactions with Python interop for complex workflows

## Best Use Cases

1. **Graph Analytics with Datalog** — Use recursive rules and built-in graph algorithms (shortest path, centrality, community detection) for relationship analytics.
2. **Temporal Data & Auditing** — Leverage time-travel queries to inspect data as it existed at any historical point, ideal for audit trails and compliance.
3. **Knowledge Graphs** — Build knowledge graphs with deductive reasoning, where new facts are inferred from existing data through Datalog rules.

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| Python | [`recipe_datalog_queries.py`](python/src/recipe_datalog_queries.py) | Create relations, insert data, run recursive Datalog queries |
| Python | [`recipe_graph_algorithms.py`](python/src/recipe_graph_algorithms.py) | Build a social graph and run shortest path and centrality algorithms |

## Limitations & Caveats

- Datalog syntax differs significantly from SQL; users must learn CozoScript's rule-based query model.
- Python client requires the `cozo-embedded` native library (Rust-based), which may not be available on all platforms.
- Embedded mode uses SQLite or RocksDB backends — the SQLite backend is single-writer; use RocksDB for higher write concurrency.
- Vector search features in embedded mode may have different coverage compared to the standalone server.
- MPL-2.0 license requires sharing changes to CozoDB itself, though proprietary applications may embed it freely.

## Further Reading

- [Official Documentation](https://docs.cozodb.org/)
- [Source Repository](https://github.com/cozodb/cozo)
- [Benchmarks](https://www.cozodb.org/benchmarks.html)
