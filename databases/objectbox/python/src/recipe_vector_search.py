"""
Recipe: Vector Search with Object Persistence
Database: ObjectBox
Description: Demonstrates defining an entity with an embedding vector,
             inserting objects, and performing vector similarity search.

Usage: python src/recipe_vector_search.py
"""

import os
import tempfile

from objectbox import Entity, Float32Vector, HnswIndex, Id, Store, String


@Entity()
class Document:
    id = Id
    text = String
    # Attach an HNSW index directly to the vector property for fast nearest-neighbor search
    embedding = Float32Vector(index=HnswIndex(dimensions=4))


def main():
    # 1. Setup -- create a temporary ObjectBox store
    tmpdir = tempfile.mkdtemp(prefix="objectbox_recipe_")
    db_dir = os.path.join(tmpdir, "vector_search_db")

    store = Store(directory=db_dir)
    box = store.box(Document)

    # 2. Write -- insert documents with embeddings
    docs_data = [
        ("ObjectBox is an on-device vector database", [0.1, 0.2, 0.3, 0.4]),
        ("Vector search enables semantic similarity", [0.9, 0.8, 0.7, 0.6]),
        ("Embedded databases run without a server", [0.15, 0.25, 0.35, 0.45]),
        ("Python is great for data science and AI", [0.85, 0.75, 0.65, 0.55]),
        ("IoT devices need efficient local storage", [0.12, 0.22, 0.32, 0.42]),
    ]

    inserted_ids = []
    for text, emb in docs_data:
        doc = Document()
        doc.text = text
        doc.embedding = emb
        obj_id = box.put(doc)
        inserted_ids.append(obj_id)

    print(f"Inserted {len(inserted_ids)} documents")
    print(f"IDs: {inserted_ids}")

    # 3. Read -- retrieve specific document by ID
    doc = box.get(inserted_ids[0])
    print(f"\nRetrieved doc[0]: {doc.text}")

    # 4. Vector search -- find documents nearest to a query vector
    query_embedding = [0.1, 0.2, 0.3, 0.4]

    qb = box.query()
    qb.nearest_neighbors_f32(Document.embedding, query_embedding, 3)
    query = qb.build()
    results = query.find()

    print(f"\nTop {len(results)} nearest neighbors to query vector:")
    for i, result in enumerate(results):
        print(f"  {i+1}. [id={result.id}] {result.text}")

    # 5. Cleanup
    store.close()
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)
    print(f"\nCleaned up {tmpdir}")


if __name__ == "__main__":
    main()
