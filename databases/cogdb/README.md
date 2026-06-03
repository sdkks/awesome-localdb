# CogDB

> **Category:** Graph | **License:** Apache-2.0 | **Stars:** ~359

## Overview

CogDB is a persistent, embedded graph database for Python with zero setup. It is a triple store that models data as subject-predicate-object triples and provides Torque, a fluent chainable Python API for graph traversal. CogDB includes SIMD-accelerated vector similarity search, supports loading pre-trained embeddings (GloVe, Gensim), and can serve graphs over HTTP. It runs in-process with no server required and works in notebooks, apps, and browsers via Pyodide.

## Quick Start

### Python

```python
# Install: pip install cogdb
from cog.torque import Graph

# Create a graph and add triples
g = Graph("social")
g.put("alice", "follows", "bob")
g.put("bob", "follows", "charlie")
g.put("bob", "status", "active")

# Traverse with Torque
g.v("alice").out("follows").all()             # {'result': [{'id': 'bob'}]}
g.v().has("status", "active").all()           # {'result': [{'id': 'bob'}]}
g.v("alice").out("follows").out("follows").all()  # {'result': [{'id': 'charlie'}]}

# Vector search
g.put_embedding("alice", [0.9, 0.8, 0.2, 0.1])
g.put_embedding("bob",   [0.85, 0.75, 0.25, 0.15])
g.v().k_nearest("alice", k=2).all()           # {'result': [{'id': 'alice'}, {'id': 'bob'}]}
```

## On-Disk Format

Persistent key-value store under COG_HOME directory (default `/tmp/cog-test`)

## Core Strengths

- Zero-setup embedded triple store with fluent Torque traversal API
- Built-in SIMD-accelerated vector similarity search via SimSIMD
- Load pre-trained embeddings (GloVe, Gensim) in a single line
- Combine graph traversal with vector similarity in one query pipeline
- HTTP server mode for remote graph access
- Runs in browser via Pyodide for interactive notebooks

## Best Use Cases

1. **Lightweight Knowledge Graphs** -- Store RDF-style triples and traverse relationships with a chainable Python API.
2. **Semantic Search** -- Combine graph traversal with vector similarity for hybrid retrieval.
3. **Interactive Notebooks** -- Embed graph processing in Jupyter/Colab with zero configuration.

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| Python | [`recipe_graph_triples.py`](python/src/recipe_graph_triples.py) | Create a social graph with triples, run Torque traversal queries |
| Python | [`recipe_vector_search.py`](python/src/recipe_vector_search.py) | Store embeddings on graph vertices, run similarity search and k-NN |

## Limitations & Caveats

- CogDB is a triple store, not a property graph database -- data is modeled as subject-predicate-object triples rather than nodes with rich properties.
- No transactional guarantees beyond single-put atomicity.
- Vector search operates on a single flat index per graph; no HNSW or disk-backed vector index.
- The fluent Torque API is Python-only; there are no client bindings for other languages.
- In-memory performance degrades with very large graphs (100k+ triples) unless using disk persistence.

## Further Reading

- [Official Documentation](https://cogdb.io)
- [Source Repository](https://github.com/arun1729/cog)
