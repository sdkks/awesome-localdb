"""Tests for recipe_vector_search.py"""

import libsql_experimental as libsql
import math
import os
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from recipe_vector_search import (
    main,
    vector_to_blob,
    blob_to_vector,
    cosine_similarity,
)


def test_recipe_runs_without_error():
    """The recipe should execute without raising an exception."""
    main()


def test_vector_blob_roundtrip():
    """Packing and unpacking vectors via BLOB should be lossless."""
    original = [0.1, 0.5, -0.3, 0.9, 0.0]
    blob = vector_to_blob(original)
    restored = blob_to_vector(blob)
    assert len(restored) == len(original)
    for a, b in zip(original, restored):
        assert abs(a - b) < 1e-10


def test_cosine_similarity_identical():
    """Cosine similarity of identical vectors should be 1.0."""
    v = [0.3, 0.4, 0.9]
    sim = cosine_similarity(v, v)
    assert abs(sim - 1.0) < 1e-10


def test_cosine_similarity_orthogonal():
    """Cosine similarity of orthogonal vectors should be 0.0."""
    a = [1.0, 0.0, 0.0]
    b = [0.0, 1.0, 0.0]
    sim = cosine_similarity(a, b)
    assert abs(sim - 0.0) < 1e-10


def test_cosine_similarity_opposite():
    """Cosine similarity of opposite vectors should be -1.0."""
    a = [1.0, 0.0]
    b = [-1.0, 0.0]
    sim = cosine_similarity(a, b)
    assert abs(sim - (-1.0)) < 1e-10


def test_store_and_retrieve_embeddings():
    """Embeddings stored as BLOBs should be retrievable and searchable."""
    db = libsql.connect(":memory:")

    db.execute("""
        CREATE TABLE embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            vector BLOB NOT NULL,
            dimensions INTEGER NOT NULL
        )
    """)

    samples = [
        ("alpha", [1.0, 0.0, 0.0]),
        ("beta", [0.0, 1.0, 0.0]),
        ("gamma", [0.0, 0.0, 1.0]),
    ]

    for text, vec in samples:
        blob = vector_to_blob(vec)
        db.execute(
            "INSERT INTO embeddings (text, vector, dimensions) VALUES (?, ?, ?)",
            (text, blob, len(vec)),
        )

    # Query: find nearest to [1.0, 0.1, 0.0]
    query_vec = [1.0, 0.1, 0.0]
    rows = db.execute("SELECT id, text, vector FROM embeddings").fetchall()

    best_text = None
    best_sim = -2.0
    for row in rows:
        _, text, blob = row
        stored_vec = blob_to_vector(blob)
        sim = cosine_similarity(query_vec, stored_vec)
        if sim > best_sim:
            best_sim = sim
            best_text = text

    assert best_text == "alpha"
    assert best_sim > 0.9

    db.close()
