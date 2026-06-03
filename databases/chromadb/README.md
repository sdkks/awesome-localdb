# ChromaDB

> **Category:** Vector | **License:** Apache-2.0 | **Stars:** ~18k

## Overview

ChromaDB is an open-source embedding database purpose-built for AI applications. It runs embedded in Python by default, providing a developer-friendly API with automatic text-to-vector conversion. Widely adopted in the LangChain and LlamaIndex ecosystems, ChromaDB organizes data into collections that store documents, embeddings, and metadata together, enabling vector similarity search with flexible filtering. A client-server mode is available when you need to scale beyond a single process.

## Quick Start

### Python

```python
# Install: pip install chromadb
import chromadb

# Connect / open (ephemeral in-memory by default)
client = chromadb.Client()

# Create a collection
collection = client.create_collection(name="my_docs")

# Add documents with embeddings
collection.add(
    ids=["doc1", "doc2"],
    documents=["pineapple pizza recipe", "orange juice recipe"],
    metadatas=[{"category": "food"}, {"category": "drink"}],
)

# Query by text
results = collection.query(
    query_texts=["tropical fruit"],
    n_results=2,
)
print(results["documents"])
```

## On-Disk Format

SQLite-backed (Single File) when persistent; ephemeral in-memory by default

## Core Strengths

- Zero-configuration embedded mode with no external process required
- Built-in embedding function with automatic text-to-vector conversion
- Collection-based organization for separating document groups
- Metadata-aware filtering combined with vector similarity search
- First-class integration with LangChain, LlamaIndex, and AI frameworks
- Ephemeral in-memory mode for rapid prototyping and testing

## Best Use Cases

1. **RAG Pipelines** -- Store document chunks and embeddings for retrieval-augmented generation with LLMs.
2. **Semantic Search** -- Query documents by meaning rather than keywords, with metadata filtering.
3. **AI Prototyping** -- Get started with vector storage in a single Python process with no infrastructure.

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| Python | [`recipe_vector_search.py`](python/src/recipe_vector_search.py) | Add documents with embeddings, query by similarity, metadata filtering |
| Python | [`recipe_collection_management.py`](python/src/recipe_collection_management.py) | Create, list, inspect, and delete collections |

## Limitations & Caveats

- The default embedding function downloads the all-MiniLM-L6-v2 model (~80 MB) on first use.
- Ephemeral in-memory mode is non-persistent -- use `PersistentClient` with a path for durability.
- Large-scale production deployments may benefit from running the ChromaDB server process separately.

## Further Reading

- [Official Documentation](https://docs.trychroma.com)
- [Source Repository](https://github.com/chroma-core/chroma)
