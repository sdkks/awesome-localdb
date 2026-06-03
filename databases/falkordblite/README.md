# FalkorDBLite

> **Category:** Graph | **License:** BSD-3-Clause | **Stars:** ~100

## Overview

FalkorDBLite is an embedded, zero-configuration graph database for Python. It bundles a self-contained Redis server with the FalkorDB graph module, providing full Cypher query support without any external daemon. Built as a fork of Yahoo's redislite, it auto-manages the server lifecycle and persists graph data to a single file on disk.

## Quick Start

### Python

```python
# Install: pip install falkordblite
from redislite.falkordb_client import FalkorDB

# Create or open an embedded database
db = FalkorDB("/tmp/social.db")

# Select a graph
g = db.select_graph("social")

# Create nodes and relationships with Cypher
g.query("CREATE (:Person {name: 'Alice', age: 30})")
g.query("CREATE (:Person {name: 'Bob', age: 25})")
g.query("""
  MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'})
  CREATE (a)-[:KNOWS]->(b)
""")

# Query the graph
result = g.query("MATCH (p:Person) RETURN p.name, p.age ORDER BY p.name")
for row in result.result_set:
    print(f"{row[0]}, age {row[1]}")

# Clean up
g.delete()
```

## On-Disk Format

Redis RDB (Single File + Sub-Process Server)

## Core Strengths

- Cypher query language for expressive graph pattern matching
- Zero-configuration embedded deployment with no external daemon
- Self-contained Redis server with FalkorDB module auto-managed
- Persistent graph storage between sessions
- Supports multiple independent graphs in a single database

## Best Use Cases

1. **Local Development and Testing** -- Build and test Cypher graph applications without Docker or server setup.
2. **Graph-Based AI Memory** -- Use as a local knowledge graph store for AI agents and RAG pipelines.
3. **Quick Prototyping** -- Model property graphs and relationships in Python applications with minimal setup.

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| Python | [`recipe_graph_cypher.py`](python/src/recipe_graph_cypher.py) | Create a social graph with Cypher queries and traverse relationships |

## Limitations & Caveats

- Requires Python 3.12 or higher.
- Spawns a Redis sub-process managed by the Python bindings (not purely in-process).
- On macOS, the OpenMP runtime (`libomp`) must be installed via Homebrew.
- The graph module is imported from `redislite.falkordb_client`, not a top-level `falkordblite` package.
- Based on redislite; may inherit Redis memory and persistence characteristics.

## Further Reading

- [FalkorDBLite Documentation](https://docs.falkordb.com/operations/falkordblite/falkordblite-py.html)
- [Source Repository](https://github.com/FalkorDB/falkordblite)
- [FalkorDB Website](https://www.falkordb.com/)
