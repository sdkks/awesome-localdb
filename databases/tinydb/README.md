# TinyDB

> **Category:** Document | **License:** MIT | **Stars:** ~7,000

## Overview

TinyDB is a lightweight, document-oriented database written in pure Python. It stores data as JSON and provides a clean, ORM-like query interface. TinyDB is ideal for small-scale applications, CLI tools, and prototyping where setting up a full database is overkill. It is schema-less, making it easy to get started without defining a data model upfront.

## Quick Start

### Python

```python
# Install: pip install tinydb
from tinydb import TinyDB, Query

# Connect / open
db = TinyDB("mydb.json")

# Write
db.insert({"name": "Alice", "age": 30})
db.insert({"name": "Bob", "age": 25})

# Search
User = Query()
results = db.search(User.name == "Alice")
print(results)  # [{"name": "Alice", "age": 30}]

# Update
db.update({"age": 31}, User.name == "Alice")

# Query with conditions
adults = db.search(User.age > 18)
```

## On-Disk Format

Plain Text JSON File

## Core Strengths

- 100% pure Python, no external compilation required
- Clean document-oriented API with ORM-like query builder
- Schema-less -- insert any JSON structure without migrations
- Extensible via custom storages and middleware
- Table-level organization for separating concerns
- Built-in upsert, update operations, and document IDs

## Best Use Cases

1. **Configuration Storage** -- Store app settings, preferences, and runtime configuration in a structured but simple format.
2. **Prototyping** -- Rapidly build and iterate on data models without schema constraints or server setup.
3. **Small Desktop/CLI Apps** -- Persist local state for command-line tools and desktop applications with zero setup.
4. **Scripts and Notebooks** -- Quick data persistence for Python scripts and Jupyter notebooks without external services.

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| Python | [`recipe_document_store.py`](python/src/recipe_document_store.py) | Basic document CRUD with Query() builder |
| Python | [`recipe_config_database.py`](python/src/recipe_config_database.py) | Configuration store with table separation |

## Limitations & Caveats

- Loads the entire JSON file into RAM on startup; unsuitable for large datasets
- No built-in indexing; query performance degrades with document count
- Not designed for concurrent access from multiple processes
- All data must be JSON-serializable (no binary blobs or custom types)

## Further Reading

- [Official Documentation](https://tinydb.readthedocs.io)
- [Source Repository](https://github.com/msiemens/tinydb)
