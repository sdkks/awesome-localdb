"""Tests for recipe_vector_search.py"""

import os
import tempfile

from objectbox import Entity, Float32Vector, HnswIndex, Id, Store, String

from src.recipe_vector_search import main


@Entity()
class Doc:
    id = Id
    text = String
    embedding = Float32Vector(index=HnswIndex(dimensions=4))


def test_recipe_runs_without_error():
    """The recipe should execute without raising an exception."""
    main()


def test_create_store_and_insert():
    """Verify store creation and object insertion."""
    tmpdir = tempfile.mkdtemp(prefix="objectbox_test_")
    db_dir = os.path.join(tmpdir, "test_insert_db")

    store = Store(directory=db_dir)
    box = store.box(Doc)

    # Insert documents via instance objects
    test_docs = [
        ("Document A", [1.0, 0.0, 0.0, 0.0]),
        ("Document B", [0.0, 1.0, 0.0, 0.0]),
        ("Document C", [0.0, 0.0, 1.0, 0.0]),
    ]
    ids = []
    for text, emb in test_docs:
        d = Doc()
        d.text = text
        d.embedding = emb
        ids.append(box.put(d))

    assert len(ids) == 3
    assert len(set(ids)) == 3  # all IDs should be unique

    # Verify retrieval
    retrieved = box.get(ids[0])
    assert retrieved.text == "Document A"

    store.close()
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)


def test_vector_search():
    """Vector search should return results ordered by proximity to query."""
    tmpdir = tempfile.mkdtemp(prefix="objectbox_test_")
    db_dir = os.path.join(tmpdir, "test_search_db")

    store = Store(directory=db_dir)
    box = store.box(Doc)

    # Insert documents with distinct embeddings
    test_docs = [
        ("near", [0.9, 0.1, 0.1, 0.1]),
        ("mid", [0.5, 0.5, 0.5, 0.5]),
        ("far", [0.1, 0.9, 0.1, 0.1]),
    ]
    for text, emb in test_docs:
        d = Doc()
        d.text = text
        d.embedding = emb
        box.put(d)

    # Query with a vector close to "near"
    qb = box.query()
    qb.nearest_neighbors_f32(Doc.embedding, [1.0, 0.0, 0.0, 0.0], 3)
    query = qb.build()
    results = query.find()

    assert len(results) == 3
    # The first result should be "near" (closest to query)
    assert results[0].text == "near"

    store.close()
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)
