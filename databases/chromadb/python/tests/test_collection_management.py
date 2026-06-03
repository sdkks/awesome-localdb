"""Tests for recipe_collection_management.py"""

import chromadb

from src.recipe_collection_management import main


def test_recipe_runs_without_error():
    """The recipe should execute without raising an exception."""
    main()


def test_create_list_delete_collections():
    """Verify collection CRUD: create, list, get_or_create, and delete."""
    client = chromadb.Client()

    prefix = "test_crud_"
    alpha_name = f"{prefix}alpha"
    beta_name = f"{prefix}beta"
    gamma_name = f"{prefix}gamma"

    client.create_collection(name=alpha_name)
    client.create_collection(name=beta_name)

    collections = client.list_collections()
    names = {c.name for c in collections}
    assert alpha_name in names
    assert beta_name in names

    beta = client.get_or_create_collection(name=beta_name)
    assert beta.name == beta_name

    gamma = client.get_or_create_collection(name=gamma_name)
    assert gamma.name == gamma_name
    names = {c.name for c in client.list_collections()}
    assert gamma_name in names

    client.delete_collection(name=alpha_name)
    remaining = {c.name for c in client.list_collections()}
    assert alpha_name not in remaining
    assert beta_name in remaining
    assert gamma_name in remaining

    # Clean up created test collections
    client.delete_collection(name=beta_name)
    client.delete_collection(name=gamma_name)


def test_collection_count():
    """Verify collection count after adding documents."""
    client = chromadb.Client()
    collection = client.create_collection(name="count_test")

    import numpy as np

    dim = 16
    n = 42
    rng = np.random.default_rng(1)
    embeddings = rng.normal(size=(n, dim)).tolist()
    ids = [f"d_{i}" for i in range(n)]

    collection.add(ids=ids, embeddings=embeddings)
    assert collection.count() == n
