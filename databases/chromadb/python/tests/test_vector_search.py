"""Tests for recipe_vector_search.py"""

import chromadb
import numpy as np

from src.recipe_vector_search import main


def test_recipe_runs_without_error():
    """The recipe should execute without raising an exception."""
    main()


def test_create_collection_and_search():
    """Verify collection creation, document count, and vector search return expected results."""
    client = chromadb.Client()
    collection = client.create_collection(name="test_docs")

    dim = 64
    rng = np.random.default_rng(13)
    num_docs = 20

    embeddings = rng.normal(size=(num_docs, dim)).tolist()
    ids = [f"doc_{i}" for i in range(num_docs)]
    documents = [f"Test document {i}" for i in range(num_docs)]
    metadatas = [{"kind": "a" if i < 10 else "b"} for i in range(num_docs)]

    collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
    assert collection.count() == num_docs

    query_embedding = rng.normal(size=dim).tolist()
    results = collection.query(query_embeddings=[query_embedding], n_results=3)
    assert len(results["ids"][0]) == 3
    assert len(results["documents"][0]) == 3
    assert len(results["distances"][0]) == 3


def test_vector_search_with_metadata_filter():
    """Vector search with metadata filter should return only matching rows."""
    client = chromadb.Client()
    collection = client.create_collection(name="test_filter")

    dim = 32
    rng = np.random.default_rng(42)
    num_docs = 20

    embeddings = rng.normal(size=(num_docs, dim)).tolist()
    ids = [f"item_{i}" for i in range(num_docs)]
    metadatas = [{"color": "red" if i < 10 else "blue"} for i in range(num_docs)]

    collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas)

    query_embedding = rng.normal(size=dim).tolist()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=10,
        where={"color": "red"},
    )
    # All returned metadatas should have color "red"
    for meta in results["metadatas"][0]:
        assert meta["color"] == "red"
